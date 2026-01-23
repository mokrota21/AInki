from fastapi import FastAPI, UploadFile, HTTPException, status
from fastapi import BackgroundTasks as FastAPIBackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src import settings, DefaultReader, FileReader, Chunker, DefaultChunker, Docs, DocsMetadata, Chunks, TaskStatus, Knowledge
from src.workflows import add_book_background, extract_knowledge_background, create_task
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select, update
import uuid
from fastapi.security import OAuth2PasswordBearer
from io import BytesIO
import uvicorn

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
NAMESPACE = uuid.UUID(settings.namespace)

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

async def lock_the_task(task_id: uuid.UUID):
    """
    Locks the task so that only one instance of the task can run at a time.
    Atomically handles creation of the task if it doesn't exist.
    """
    await create_task(task_id, "created")
    
    engine = settings.get_pg_engine()
    with Session(engine) as session:
        stmt = (
            update(TaskStatus)
            .where(
                TaskStatus.task_id == task_id,
                TaskStatus.status != "started"  # Only update if still "created"
            )
            .values(status="started")
        )
        try:
            result = session.execute(stmt)
            session.commit()
            if result.rowcount == 0:
                return {"message": "Task already locked!", "status": "locked" } # It means task is already running and we should not proceed
        except Exception as e:
            logger.error(f"Failed to update task: {e}", exc_info=True)
            return {"message": "Failed to lock task!", "status": "error"} # It means there was an error. Ideally raise an error and check out what is wrong
    return {"message": "Task locked successfully!", "status": "success"} # It means task was locked succesfully and we can proceed


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/add-book")
async def add_book(book: UploadFile, background_tasks: FastAPIBackgroundTasks, force: bool = False):
    """
    Processes book and stores it in the server.
    """
    task_id = uuid.uuid5(NAMESPACE, book.filename)
    response = await lock_the_task(task_id)
    if response['status'] == "locked":
        return {"message": response['message'], "task_id": task_id}
    elif response['status'] == "error":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response['message'])
    elif response['status'] == "success":
        pass
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected response from lock_the_task")
    # Read file content BEFORE passing to background task
    # UploadFile can only be read once, so we need to read it here
    file_bytes = await book.read()
    filename = book.filename
    
    _, user_id = get_user()
    # Pass file_bytes and filename instead of UploadFile object
    background_tasks.add_task(add_book_background, file_bytes, filename, user_id, force, task_id)
    
    logger.info(f"Task {task_id} - Book processing started in background")
    return {"message": response['message'], "task_id": task_id}

@app.post("/extract-knowledge")
async def extract_knowledge(doc_id: uuid.UUID, background_tasks: FastAPIBackgroundTasks):
    """
    Extracts knowledge from a book.
    """
    task_id = uuid.uuid5(NAMESPACE, str(doc_id))

    response = await lock_the_task(task_id)
    if response['status'] == "locked":
        return {"message": response['message'], "task_id": task_id}
    elif response['status'] == "error":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response['message'])
    elif response['status'] == "success":
        pass
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected response from lock_the_task")

    background_tasks.add_task(extract_knowledge_background, doc_id, task_id)
    return {"message": response['message'], "task_id": task_id}

@app.get("/fetch-user-books")
async def fetch_user_books():
    """
    Returns a list of metadata for all books in user's library.
    """
    engine = settings.get_pg_engine()
    _, user_id = get_user()
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

@app.get("/get-book-questions")
async def get_book_questions(doc_id: uuid.UUID, page_no: int):
    """
    Returns a list of questions for a given book up to the current page.
    Joins Knowledge with Chunks to filter by page_no.
    """
    engine = settings.get_pg_engine()
    with Session(engine) as session:
        # Join Knowledge with Chunks to filter by page_no
        stmt = (
            select(
                Knowledge.knowledge_id,
                Knowledge.knowledge_name,
                Knowledge.knowledge_question,
                Knowledge.chunk_no,
                Chunks.page_no
            )
            .join(Chunks, Knowledge.chunk_no == Chunks.chunk_no)
            .where(
                Knowledge.doc_id == doc_id,
                Chunks.doc_id == doc_id,
                Chunks.page_no <= page_no
            )
        )
        result = session.execute(stmt).mappings().all()
        questions = [dict(row) for row in result]
    return questions

from fastapi.responses import JSONResponse
@app.get("/health")
async def main_health():
    return JSONResponse(content={"status": "ok", "service": "Main App"})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")