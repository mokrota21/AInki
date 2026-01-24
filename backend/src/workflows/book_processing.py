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
from .update_task import update_task
import importlib.util
from pathlib import Path

from ..llm_agent import analyze_chunks_parallel

from sqlalchemy import select

logger = logging.getLogger("book_processing")


async def step_check_file_exists(filename: str, user_id: uuid.UUID, reader_name: str, force: bool) -> Tuple[bool, str]:
    """
    Step 1: Check if file already exists in storage and database
    
    Returns:
        Tuple of (should_proceed, message)
    """
    # Check blob storage
    container_client = settings.container_client
    blob_client = container_client.get_blob_client(filename)
    
    if not force and blob_client.exists():
        logger.warning(f"Attempting to upload existing file {filename} in blob storage")
        return False, "File with the same name exists in storage! Rename and try again or use force=True."
    
    # Check database for existing document
    if not force:
        engine = settings.get_pg_engine()
        with Session(engine) as session:
            stmt = select(Docs).where(
                Docs.file_name == filename,
                Docs.user_id == user_id,
                Docs.filereader == reader_name
            ).limit(1)
            existing = session.execute(stmt).first()
            if existing:
                logger.warning(f"Attempting to upload existing file {filename} in database")
                return False, "File with the same name already exists in database! Rename and try again or use force=True."
    
    return True, "File check passed"


async def step_read_file(file_bytes: bytes, filename: str) -> Tuple[List[str], bytes]:
    """
    Step 2: Read and process file with reader
    
    Args:
        file_bytes: File content as bytes
        filename: Name of the file (for determining file type)
    
    Returns:
        Tuple of (pages, file_bytes)
    """
    logger.info(f"Processing {filename} with OCR...")
    try:
        reader = DefaultReader()
        file_type = filename.split('.')[-1] if '.' in filename else None
        pages = reader.get_md(file_bytes, file_type)
        logger.info(f"OCR completed - {len(pages)} pages extracted")
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
    logger.info("Chunking content...")
    try:
        chunker = DefaultChunker()
        chunks = chunker.chunk(pages)
        logger.info(f"Created {len(chunks)} chunks")
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
    logger.info(f"Uploading to storage...")
    try:
        container_client = settings.container_client
        blob_client = container_client.get_blob_client(filename)
        blob_client.upload_blob(file_bytes, overwrite=force)
        logger.info(f"Upload complete")
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
    reader_name: str,
    force: bool = False
):
    """
    Step 5: Save document pages to database
    """
    logger.info(f"Saving {len(pages)} pages for: {filename}")
    try:
        engine = settings.get_pg_engine()
        with Session(engine) as session:
            # If force=True, delete existing docs first
            if force:
                stmt = select(Docs).where(
                    Docs.file_name == filename,
                    Docs.user_id == user_id,
                    Docs.filereader == reader_name
                )
                existing_docs = session.execute(stmt).scalars().all()
                for doc in existing_docs:
                    session.delete(doc)
                session.flush()
            
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
        logger.info(f"Successfully saved {len(pages)} pages")
    except Exception as e:
        logger.error(f"Failed to save docs: {e}", exc_info=True)
        # Check if it's a unique constraint violation
        error_str = str(e).lower()
        if "unique" in error_str or "duplicate" in error_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"File '{filename}' already exists for this user. Use force=True to overwrite."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save document pages: {str(e)}"
        )


async def step_save_metadata(
    doc_id: uuid.UUID,
    user_id: uuid.UUID,
    pages_total: int,
    filename: str,
    reader_name: str,
    force: bool = False
):
    """
    Step 6: Save document metadata to database
    """
    logger.info("Saving metadata...")
    try:
        engine = settings.get_pg_engine()
        with Session(engine) as session:
            # If force=True, delete existing metadata first
            if force:
                stmt = select(DocsMetadata).where(
                    DocsMetadata.file_name == filename,
                    DocsMetadata.user_id == user_id,
                    DocsMetadata.filereader == reader_name
                )
                existing_metadata = session.execute(stmt).scalars().first()
                if existing_metadata:
                    session.delete(existing_metadata)
                    session.flush()
            
            doc_metadata = DocsMetadata(
                doc_id=doc_id,
                user_id=user_id,
                pages_total=pages_total,
                filereader=reader_name,
                file_name=filename
            )
            session.add(doc_metadata)
            session.commit()
        logger.info("Metadata saved")
    except Exception as e:
        logger.error(f"Failed to save metadata: {e}", exc_info=True)
        # Check if it's a unique constraint violation
        error_str = str(e).lower()
        if "unique" in error_str or "duplicate" in error_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"File '{filename}' metadata already exists for this user. Use force=True to overwrite."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save document metadata: {str(e)}"
        )


async def step_save_chunks(
    doc_id: uuid.UUID,
    chunks: List[Dict],
    chunker_name: str,
    force: bool = False
) -> Dict[str, uuid.UUID]:
    """
    Step 7: Save chunks to database
    
    Returns:
        Dictionary mapping chunk content to chunk_id
    """
    logger.info(f"Saving {len(chunks)} chunks...")
    try:
        engine = settings.get_pg_engine()
        chunk_no = 0
        last_page = -1
        chunk_id_map = {}  # Maps chunk content to chunk_id
        
        with Session(engine) as session:
            if force:
                stmt = select(Chunks).where(
                    Chunks.doc_id == doc_id
                )
                existing_chunks = session.execute(stmt).scalars().all()
                for chunk in existing_chunks:
                    session.delete(chunk)
                session.flush()
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
        logger.info(f"{len(chunks)} chunks saved")
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
        chunk_texts = [chunk['md_content'] for chunk in chunks]
        chunk_references = [chunk['chunk_no'] for chunk in chunks]  # Use text as reference to map back
        
        # Analyze chunks in parallel
        agent_response = await analyze_chunks_parallel(
            chunks=chunk_texts,
            chunk_references=chunk_references,
            batch_size=batch_size,
            max_concurrent=max_concurrent
        )

        total_knowledge_objects = 0
        
        # Save knowledge items to database
        engine = settings.get_pg_engine()
        with Session(engine) as session:
            for knowledge_item in agent_response:
                # Map reference back to chunk_id
                chunk_no = knowledge_item.reference
                
                if chunk_no is None:
                    logger.warning(f"Could not find chunk_no for reference")
                    continue

                chunk_analysis = knowledge_item.knowledge_objects
                for question in chunk_analysis.questions:
                    knowledge_row = Knowledge(
                        doc_id=doc_id,
                        chunk_no=chunk_no,
                        knowledge_name=question.knowledge_object,
                        knowledge_question=question.question
                    )
                    session.add(knowledge_row)
                    total_knowledge_objects += 1
            
            session.commit()
        logger.info(f"Generated {total_knowledge_objects} knowledge items")
        
    except Exception as e:
        logger.error(f"Failed to generate knowledge: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate knowledge: {str(e)}"
        )

async def _get_chunks(doc_id: uuid.UUID):
    """
    Gets chunks from the database.
    """
    try:
        engine = settings.get_pg_engine()
        with Session(engine) as session:
            stmt = select(*Chunks.__table__.columns).limit(10).where(Chunks.doc_id == doc_id)
            chunks = session.execute(stmt).mappings().all()
            return chunks
    except Exception as e:
        logger.error(f"Failed to get chunks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chunks: {str(e)}"
        )

async def _filter_processed_chunks(chunks: List[Dict], doc_id: uuid.UUID):
    """
    Filters out processed chunks.
    """
    try:
        engine = settings.get_pg_engine()
        chunk_nos = [chunk['chunk_no'] for chunk in chunks]
        with Session(engine) as session:
            existing_chunk_nos = {
                row[0]
                for row in session.query(Knowledge.chunk_no)
                .filter(Knowledge.doc_id == doc_id, Knowledge.chunk_no.in_(chunk_nos))
                .all()
            }

            return [chunk for chunk in chunks if chunk['chunk_no'] not in existing_chunk_nos]
    except Exception as e:
        logger.error(f"Failed to filter processed chunks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to filter processed chunks: {str(e)}"
        )

async def extract_knowledge_background(doc_id: uuid.UUID, task_id: uuid.UUID = None):
    """
    Extracts knowledge from a book.
    """
    try:
        # Step 1: Get chunks
        chunks = await _get_chunks(doc_id)
        # Step 2: Filter out processed chunks
        chunks = await _filter_processed_chunks(chunks, doc_id)
        # Step 2: Generate knowledge
        await step_generate_knowledge(doc_id, chunks)
        # Step 3: Update task
        await update_task(task_id, "completed")
    except Exception as e:
        logger.error(f"Failed to extract knowledge: {e}", exc_info=True)
        await update_task(task_id, "failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract knowledge: {str(e)}"
        )

async def add_book_background(file_bytes: bytes, filename: str, user_id: uuid.UUID, force: bool = False, task_id: uuid.UUID = None):
    """
    Stores book in blob storage and processes it with OCR. Results are saved to the database.
    
    Args:
        file_bytes: File content as bytes (read before passing to background task)
        filename: Name of the file
        user_id: User ID
        force: Whether to overwrite existing files
        task_id: Task ID for tracking
    """
    logger.info(f"Task {task_id} - Starting book processing for: {filename}")
    
    try:

        reader = DefaultReader()
        chunker = DefaultChunker()
        doc_id = uuid.uuid4()

        # Step 1: Check if file exists
        should_proceed, message = await step_check_file_exists(filename, user_id, reader.name, force)
        if not should_proceed:
            await update_task(task_id, "failed")
            return {"message": message, "doc_id": None}

        # Step 2: Read file
        pages, file_bytes = await step_read_file(file_bytes, filename)
        
        # Step 3: Chunk content
        chunks = await step_chunk_content(pages)

        # Step 4: Upload to storage
        await step_upload_to_storage(filename, file_bytes, force)

        # Step 5: Save docs
        await step_save_docs(doc_id, user_id, pages, filename, reader.name, force)

        # Step 6: Save metadata
        await step_save_metadata(doc_id, user_id, len(pages), filename, reader.name, force)

        # Step 7: Save chunks
        await step_save_chunks(doc_id, chunks, chunker.name)

        # Step 8: Update task
        await update_task(task_id, "completed")

    except Exception as e:
        logger.error(f"Failed to add book: {e}", exc_info=True)
        await update_task(task_id, "failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add book: {str(e)}"
        )