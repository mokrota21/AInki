from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List
from src import *
from dotenv import load_dotenv
from datetime import datetime
import uvicorn
import logging
import traceback

load_dotenv()

app = FastAPI(title="AInki - Spaced Repetition Learning", version="1.0.0")
context_diff = 2
truncate_after = 100

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('ainki.log')  # File output
    ]
)
logger = logging.getLogger(__name__)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

readers = {
    "DefaultReader": DefaultReader,
    "PDFReader": PDFReader,
    "MineruReader": MineruReader
}

security = HTTPBearer()

# Pydantic models
class UserRegister(BaseModel):
    username: str
    password: str
    gmail: str

class UserLogin(BaseModel):
    username_or_gmail: str
    password: str

class PendingItem(BaseModel):
    node_id: str
    name: str
    content: str
    doc_id: int
    chunk_start: int
    chunk_end: int

def lifespan(app: FastAPI):
    init_graph()
    yield

# Authentication dependency
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        userid = credentials.credentials
        # Verify user exists (you might want to add a proper token validation here)
        return userid
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication")

# Routes
@app.post("/api/auth/register")
def register(user_data: UserRegister):
    try:
        userid = insert_user(user_data.gmail, user_data.password, user_data.username)
        logger.info(f"User registered successfully: {user_data.username}")
        return {"userid": userid, "message": "User registered successfully"}
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

@app.post("/api/auth/login")
def login(user_data: UserLogin):
    try:
        userid = login(user_data.password, user_data.username_or_gmail)
        if userid is None:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        logger.info(f"User logged in successfully: {user_data.username_or_gmail}")
        return {"userid": userid, "message": "Login successful"}
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")

@app.get("/api/docs")
def get_docs():
    try:
        docs = get_all_docs()
        return {"docs": docs}
    except Exception as e:
        logger.error(f"Docs error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get docs: {str(e)}")

@app.get("/api/file_content")
def get_file_content(
    doc_id: int
):
    try:
        response = {}
        _, response['name'], response['folder'] = list(get_doc(doc_id).values())
        response['chunks'] = get_chunks(doc_id)
        return response
    except Exception as e:
        logger.error(f"File content error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get file content: {str(e)}")

@app.post("/api/upload")
def upload_file(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
    reader: str = "DefaultReader"
):
    try:
        reader = readers[reader]
        logger.info(f"Uploading file: {file.filename} for user: {current_user}")
        
        # Process file using your existing pipeline

        # Read file content
        content, result_folder = reader().read_file(file)

        doc_id = insert_doc(file, result_folder, force=True)
        if doc_id == -1:
            raise HTTPException(status_code=400, detail="File already exists")
        logger.info(f"Document inserted with ID: {doc_id}")
        
        chunks = DefaultChunker().chunk(content)
        for chunk in chunks:
            insert_chunk(chunk, doc_id, chunks.index(chunk), DefaultReader().name)
        logger.info(f"Created {len(chunks)} chunks")

        # Enumerate chunks
        chunks = [(chunk, chunks.index(chunk)) for chunk in chunks]
        
        objects = extract_objects_from_chunks(chunks[:10], doc_id) # Limit for testing
        logger.info(f"Extracted {len(objects)} objects")
        
        object_nodes = insert_objects(objects)
        for object in object_nodes: merge_repetition_state(object.element_id, RepeatState(current_user, 0))
        logger.info("Objects inserted successfully")
        
        return {
            "message": "File processed successfully",
            "doc_id": doc_id,
            "chunks_count": len(chunks),
            "objects_count": len(objects)
        }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/pending", response_model=List[PendingItem])
def get_pending_items(current_user: str = Depends(get_current_user)):
    try:
        logger.info(f"Getting pending items for user: {current_user}")
        pending_records = get_all_pending(current_user)
        logger.info(f"Found {len(pending_records)} pending records")
        pending_items = []
        
        for record in pending_records:
            node = record["n"]
            content = chunk_maper(node["doc_id"], node["chunk_id_s"], node["chunk_id_e"])
            context = chunk_maper(node["doc_id"], node["chunk_id_s"] - context_diff, node["chunk_id_e"] + context_diff)
            context = context[:truncate_after] + " ... " + context[-truncate_after:] if len(context) > 2 * truncate_after else context

            pending_items.append(PendingItem(
                node_id=node.element_id,
                name=node["name"],
                content=content,
                context=context,
                doc_id=node["doc_id"],
                chunk_start=node["chunk_id_s"],
                chunk_end=node["chunk_id_e"]
            ))
        
        logger.info(f"Returning {len(pending_items)} pending items")
        return pending_items
    except Exception as e:
        logger.error(f"Pending items error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get pending items: {str(e)}")

@app.post("/api/quiz/answer")
def submit_answer(
    answer: QuizAnswer
):
    try:
        logger.info(f"Submitting answer for node {answer.node_id}, correct: {answer.correct}")
        
        # Process the answer using your existing logic
        check_answer(answer)
        logger.info("Answer processed successfully")
        
        return {"message": "Answer recorded successfully"}
    except Exception as e:
        logger.error(f"Quiz answer error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

# Debug endpoint to see all available routes
@app.get("/api/debug/routes")
def debug_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods)
            })
    return {"routes": routes}

# Debug endpoint to test logging
@app.get("/api/debug/log")
def debug_log():
    logger.info("Debug log test - INFO level")
    logger.warning("Debug log test - WARNING level")
    logger.error("Debug log test - ERROR level")
    return {"message": "Check console and ainki.log file for logs"}

# Global exception handler
@app.exception_handler(Exception)
def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return HTTPException(
        status_code=500, 
        detail=f"Internal server error: {str(exc)}"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
