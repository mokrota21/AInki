from pydoc import Doc
from fastapi import FastAPI, UploadFile, HTTPException, status
from pydantic import BaseModel
from src import settings, DefaultReader, FileReader, Chunker, DefaultChunker, Docs, Chunks
import logging
from sqlalchemy.orm import Session
import uuid

logger = logging.getLogger("tables.base")

# Configure the root logger (only if not already configured)
if not logging.root.handlers:
    logging.basicConfig(
        format="{asctime} - {name} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        level=logging.INFO
    )

app = FastAPI()
user = "mokrota"
user_id = "f7ef8cce-efe0-42da-849e-4971a7e5a573"

def get_user():
    return user, user_id

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/add-book")
# async def add_book(book: UploadFile, reader: FileReader = DefaultReader(), chunker: Chunker = DefaultChunker(), force: bool = False):
async def add_book(book: UploadFile, force: bool = False): #TODO: make dropdown of readers and chunkers
    """
    Processes file and stores it in the server.
    
    Args:
        book: The uploaded file to process and store.
    
    Returns:
        dict: Information about the stored book.
    """
    ### Check if file exists
    container_client = settings.container_client
    blob_client = container_client.get_blob_client(book.filename)
    if not force and blob_client.exists():
        logger.warning(f"Attempting to upload existing file {book.filename}")
        return {
            "message": "File with the same name exists! Rename and try again."
        }

    ### Process file with reader
    reader = DefaultReader()
    logger.info("Reading file...")
    try:
        # Read file bytes and get file type
        file_bytes = await book.read()
        file_type = book.filename.split('.')[-1] if '.' in book.filename else None
        pages = reader.get_md(file_bytes, file_type)
    except Exception as e:
        logger.error(f"Failed to read file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )
    logger.info("Success!")
    
    ### Chunk the content
    chunker = DefaultChunker()
    logger.info("Chunking file content...")
    try:
        chunks = chunker.chunk(pages)
    except Exception as e:
        logger.error(f"Failed to chunk file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )
    logger.info("Success!")

    ### Upload to storage
    logger.info("Uploading file to storage...")
    blob_client.upload_blob(file_bytes, overwrite=force)
    logger.info("Success!")

    ### Update docs database
    logger.info("Updating docs database...")
    user, user_id = get_user()
    engine = settings.get_pg_engine()
    with Session(engine) as session:
        doc_id = uuid.uuid4()
        for page_no, page in enumerate(pages):
            doc = Docs(
                doc_id=doc_id, 
                user_id=user_id, 
                md_content=page, 
                page_no=page_no, 
                filereader=reader.name, 
                file_name=book.filename)
            session.add(doc)
        session.commit()
    logger.info("Success!")

    ### Update chunks database
    logger.info("Updating chunks database...")
    chunk_no = 0
    last_page = -1
    with Session(engine) as session:
        for chunk in chunks:
            text = chunk['text']
            page_no = chunk['page_no']
            chunk_no = chunk_no + 1 if page_no == last_page else 0
            chunk_row = Chunks(
                md_content=text,
                chunk_no=chunk_no,
                doc_id=doc_id,
                chunker=chunker.name,
                page_no=page_no
            )
            session.add(chunk_row)
        session.commit()
    logger.info("Success!")
    
    return {"message": "Success!"}
