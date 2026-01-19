"""
Book processing workflow - breaks down the add_book endpoint into modular steps
"""
import uuid
import logging
from typing import Tuple, List, Dict
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from ..config.settings import settings
from .. import DefaultReader, DefaultChunker, Docs, DocsMetadata, Chunks, Knowledge
import importlib.util
from pathlib import Path

# Import llm_agent module (handling hyphen in directory name)
_llm_agent_path = Path(__file__).parent.parent / "llm-agent" / "llm_agent.py"
spec = importlib.util.spec_from_file_location("llm_agent", _llm_agent_path)
llm_agent_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llm_agent_module)
analyze_chunks_parallel = llm_agent_module.analyze_chunks_parallel
from sqlalchemy import select

logger = logging.getLogger("book_processing")


async def step_check_file_exists(filename: str, force: bool) -> Tuple[bool, str]:
    """
    Step 1: Check if file already exists in storage
    
    Returns:
        Tuple of (should_proceed, message)
    """
    container_client = settings.container_client
    blob_client = container_client.get_blob_client(filename)
    
    if not force and blob_client.exists():
        logger.warning(f"Attempting to upload existing file {filename}")
        return False, "File with the same name exists! Rename and try again."
    
    return True, "File check passed"


async def step_read_file(book: UploadFile) -> Tuple[List[str], bytes]:
    """
    Step 2: Read and process file with reader
    
    Returns:
        Tuple of (pages, file_bytes)
    """
    logger.info("Reading file...")
    try:
        reader = DefaultReader()
        file_bytes = await book.read()
        file_type = book.filename.split('.')[-1] if '.' in book.filename else None
        pages = reader.get_md(file_bytes, file_type)
        logger.info("Success!")
        return pages, file_bytes
    except Exception as e:
        logger.error(f"Failed to read file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )


async def step_chunk_content(pages: List[str]) -> List[Dict]:
    """
    Step 3: Chunk the content
    
    Returns:
        List of chunk dictionaries
    """
    logger.info("Chunking file content...")
    try:
        chunker = DefaultChunker()
        chunks = chunker.chunk(pages)
        logger.info("Success!")
        return chunks
    except Exception as e:
        logger.error(f"Failed to chunk file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )


async def step_upload_to_storage(filename: str, file_bytes: bytes, force: bool):
    """
    Step 4: Upload file to blob storage
    """
    logger.info("Uploading file to storage...")
    try:
        container_client = settings.container_client
        blob_client = container_client.get_blob_client(filename)
        blob_client.upload_blob(file_bytes, overwrite=force)
        logger.info("Success!")
    except Exception as e:
        logger.error(f"Failed to upload file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


async def step_save_docs(
    doc_id: uuid.UUID,
    user_id: uuid.UUID,
    pages: List[str],
    filename: str,
    reader_name: str
):
    """
    Step 5: Save document pages to database
    """
    logger.info("Updating docs database...")
    try:
        engine = settings.get_pg_engine()
        with Session(engine) as session:
            for page_no, page in enumerate(pages):
                doc = Docs(
                    doc_id=doc_id,
                    user_id=user_id,
                    md_content=page,
                    page_no=page_no,
                    filereader=reader_name,
                    file_name=filename
                )
                session.add(doc)
            session.commit()
        logger.info("Success!")
    except Exception as e:
        logger.error(f"Failed to save docs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save document pages: {str(e)}"
        )


async def step_save_metadata(
    doc_id: uuid.UUID,
    user_id: uuid.UUID,
    pages_total: int,
    filename: str,
    reader_name: str
):
    """
    Step 6: Save document metadata to database
    """
    logger.info("Updating docs metadata database...")
    try:
        engine = settings.get_pg_engine()
        with Session(engine) as session:
            doc_metadata = DocsMetadata(
                doc_id=doc_id,
                user_id=user_id,
                pages_total=pages_total,
                filereader=reader_name,
                file_name=filename
            )
            session.add(doc_metadata)
            session.commit()
        logger.info("Success!")
    except Exception as e:
        logger.error(f"Failed to save metadata: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save document metadata: {str(e)}"
        )


async def step_save_chunks(
    doc_id: uuid.UUID,
    chunks: List[Dict],
    chunker_name: str
) -> Dict[str, uuid.UUID]:
    """
    Step 7: Save chunks to database
    
    Returns:
        Dictionary mapping chunk content to chunk_id
    """
    logger.info("Updating chunks database...")
    try:
        engine = settings.get_pg_engine()
        chunk_no = 0
        last_page = -1
        chunk_id_map = {}  # Maps chunk content to chunk_id
        
        with Session(engine) as session:
            for chunk in chunks:
                text = chunk['text']
                page_no = chunk['page_no']
                chunk_no = chunk_no + 1 if page_no == last_page else 0
                chunk_row = Chunks(
                    md_content=text,
                    chunk_no=chunk_no,
                    doc_id=doc_id,
                    chunker=chunker_name,
                    page_no=page_no
                )
                session.add(chunk_row)
                session.flush()  # Flush to get the ID
                chunk_id_map[text] = chunk_row.id
                last_page = page_no
            session.commit()
        logger.info("Success!")
        return chunk_id_map
    except Exception as e:
        logger.error(f"Failed to save chunks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save chunks: {str(e)}"
        )


async def step_generate_knowledge(
    doc_id: uuid.UUID,
    chunks: List[Dict],
    chunk_id_map: Dict[str, uuid.UUID],
    batch_size: int = 10,
    max_concurrent: int = 5
):
    """
    Step 8: Generate knowledge from chunks using LLM agent
    
    Args:
        doc_id: Document ID
        chunks: List of chunk dictionaries with 'text' key
        chunk_id_map: Dictionary mapping chunk content to chunk_id
        batch_size: Number of chunks to process in each batch
        max_concurrent: Maximum number of concurrent LLM requests
    """
    logger.info("Generating knowledge from chunks...")
    try:
        # Extract chunk texts and create references
        chunk_texts = [chunk['text'] for chunk in chunks]
        chunk_references = [chunk['text'] for chunk in chunks]  # Use text as reference to map back
        
        # Analyze chunks in parallel
        agent_response = await analyze_chunks_parallel(
            chunks=chunk_texts,
            chunk_references=chunk_references,
            batch_size=batch_size,
            max_concurrent=max_concurrent
        )
        
        # Save knowledge items to database
        engine = settings.get_pg_engine()
        with Session(engine) as session:
            for knowledge_item in agent_response.knowledge_list:
                # Map reference back to chunk_id
                chunk_text = knowledge_item.reference
                chunk_id = chunk_id_map.get(chunk_text)
                
                if chunk_id is None:
                    logger.warning(f"Could not find chunk_id for reference: {chunk_text[:50]}...")
                    continue
                
                knowledge_row = Knowledge(
                    doc_id=doc_id,
                    chunk_id=chunk_id,
                    knowledge_name=knowledge_item.details.knowledge_object,
                    knowledge_question=knowledge_item.details.question
                )
                session.add(knowledge_row)
            
            session.commit()
        
        logger.info(f"Success! Generated {len(agent_response.knowledge_list)} knowledge items")
        
        if agent_response.errors:
            logger.warning(f"Encountered {len(agent_response.errors)} errors during knowledge generation")
            
    except Exception as e:
        logger.error(f"Failed to generate knowledge: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate knowledge: {str(e)}"
        )


async def process_book_workflow(
    book: UploadFile,
    user_id: uuid.UUID,
    force: bool = False
) -> Dict:
    """
    Orchestrates the complete book processing workflow
    
    Args:
        book: The uploaded file
        user_id: User ID for the book
        force: Whether to overwrite existing files
    
    Returns:
        Dictionary with processing results including doc_id
    """
    reader = DefaultReader()
    chunker = DefaultChunker()
    doc_id = uuid.uuid4()
    
    # Step 1: Check if file exists
    should_proceed, message = await step_check_file_exists(book.filename, force)
    if not should_proceed:
        return {"message": message, "doc_id": None}
    
    # Step 2: Read file
    pages, file_bytes = await step_read_file(book)
    
    # Step 3: Chunk content
    chunks = await step_chunk_content(pages)
    
    # Step 4: Upload to storage
    await step_upload_to_storage(book.filename, file_bytes, force)
    
    # Step 5: Save docs
    await step_save_docs(doc_id, user_id, pages, book.filename, reader.name)
    
    # Step 6: Save metadata
    await step_save_metadata(doc_id, user_id, len(pages), book.filename, reader.name)
    
    # Step 7: Save chunks
    chunk_id_map = await step_save_chunks(doc_id, chunks, chunker.name)
    
    # Step 8: Generate knowledge from chunks
    await step_generate_knowledge(doc_id, chunks, chunk_id_map)
    
    return {
        "message": "Success!",
        "doc_id": str(doc_id),
        "pages_total": len(pages),
        "chunks_total": len(chunks)
    }
