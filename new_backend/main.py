from pydoc import Doc
from fastapi import FastAPI, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src import settings, DefaultReader, FileReader, Chunker, DefaultChunker, Docs, DocsMetadata, Chunks
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid
from fastapi.security import OAuth2PasswordBearer
from io import BytesIO

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

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173"],  # Frontend dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: Replace with proper user authentication
# Currently using hardcoded user for development
# This should be replaced with JWT tokens or session-based auth
user = "mokrota"
user_id = "f7ef8cce-efe0-42da-849e-4971a7e5a573"

def get_user():
    return user, user_id

@app.get("/")
async def root():
    return {"message": "Hello World"}

from src.workflows.book_processing import process_book_workflow

@app.post("/add-book")
async def add_book(book: UploadFile, force: bool = False):
    """
    Processes file and stores it in the server.
    Uses a modular workflow pattern with separate steps.
    
    Args:
        book: The uploaded file to process and store.
        force: Whether to overwrite existing files.
    
    Returns:
        dict: Information about the stored book including doc_id.
    """
    user, user_id = get_user()
    return await process_book_workflow(book, user_id, force)

@app.get("/fetch-user-books")
async def fetch_user_books():
    """
    Returns a list of metadata for all books in user's library.
    """
    engine = settings.get_pg_engine()
    stmt = select(
        DocsMetadata.doc_id, 
        DocsMetadata.created_at, 
        DocsMetadata.pages_total,
        DocsMetadata.file_name
        ).where(DocsMetadata.user_id == user_id)
    with Session(engine) as session:
        result = session.execute(stmt).mappings().all()
        # Convert RowMapping objects to plain dicts for JSON serialization
        docs = [dict(row) for row in result]
    return docs

@app.get("/get-book")
async def get_book(filename: str):
    """
    Returns file bytes from blob storage that can be rendered by the frontend.
    
    Args:
        filename: Name of the file to retrieve from blob storage
    
    Returns:
        StreamingResponse: File bytes with appropriate content type
    """
    try:
        container_client = settings.container_client
        blob_client = container_client.get_blob_client(filename)
        
        if not blob_client.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File '{filename}' not found"
            )
        
        # Download blob as bytes
        download_stream = blob_client.download_blob()
        file_bytes = download_stream.readall()
        
        # Determine content type based on file extension
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        content_types = {
            'pdf': 'application/pdf',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'txt': 'text/plain',
            'md': 'text/markdown'
        }
        media_type = content_types.get(file_ext, 'application/octet-stream')
        
        # Return as StreamingResponse for frontend rendering
        return StreamingResponse(
            BytesIO(file_bytes),
            media_type=media_type,
            headers={"Content-Disposition": f'inline; filename="{filename}"'}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve file '{filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve file: {str(e)}"
        )
