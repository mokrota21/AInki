from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import src
import os
import asyncio
from datetime import datetime
import uvicorn
import logging
import traceback

app = FastAPI(title="AInki - Spaced Repetition Learning", version="1.0.0")

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

security = HTTPBearer()

# Pydantic models
class UserRegister(BaseModel):
    username: str
    password: str
    gmail: str

class UserLogin(BaseModel):
    username_or_gmail: str
    password: str

class QuizAnswer(BaseModel):
    node_id: str
    correct: bool

class PendingItem(BaseModel):
    node_id: str
    name: str
    content: str
    doc_id: int
    chunk_start: int
    chunk_end: int

# Initialize graph constraints
@app.on_event("startup")
async def startup_event():
    src.init_graph()

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        userid = credentials.credentials
        # Verify user exists (you might want to add a proper token validation here)
        return userid
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication")

# Routes
@app.post("/api/auth/register")
async def register(user_data: UserRegister):
    try:
        userid = src.add_user(user_data.gmail, user_data.password, user_data.username)
        logger.info(f"User registered successfully: {user_data.username}")
        return {"userid": userid, "message": "User registered successfully"}
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

@app.post("/api/auth/login")
async def login(user_data: UserLogin):
    try:
        userid = src.login(user_data.password, user_data.username_or_gmail)
        logger.info(f"User logged in successfully: {user_data.username_or_gmail}")
        return {"userid": userid, "message": "Login successful"}
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    try:
        logger.info(f"Uploading file: {file.filename} for user: {current_user}")
        
        # Read file content
        content = await file.read()
        logger.info(f"File size: {len(content)} bytes")
        
        # Process file using your existing pipeline
        doc_id = src.insert_doc(content)
        logger.info(f"Document inserted with ID: {doc_id}")
        
        chunks = src.DefaultChunker().chunk(content)
        logger.info(f"Created {len(chunks)} chunks")
        
        objects = src.extract_objects_from_chunks(chunks, doc_id)
        logger.info(f"Extracted {len(objects)} objects")
        
        src.insert_objects(objects)
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
async def get_pending_items(current_user: str = Depends(get_current_user)):
    try:
        logger.info(f"Getting pending items for user: {current_user}")
        pending_records = src.get_all_pending()
        logger.info(f"Found {len(pending_records)} pending records")
        pending_items = []
        
        for record in pending_records:
            node = record["n"]
            repetition_state = record["r"]
            
            # Get node details
            node_details = src.driver.execute_query(
                """
                MATCH (n)
                WHERE elementId(n) = $node_id
                RETURN n.name as name, n.doc_id as doc_id, 
                       n.chunk_id_s as chunk_start, n.chunk_id_e as chunk_end
                """,
                node_id=node.element_id
            )
            
            if node_details.records:
                details = node_details.records[0]
                pending_items.append(PendingItem(
                    node_id=node.element_id,
                    name=details["name"],
                    content=f"Content from chunks {details['chunk_start']}-{details['chunk_end']}",
                    doc_id=details["doc_id"],
                    chunk_start=details["chunk_start"],
                    chunk_end=details["chunk_end"]
                ))
        
        logger.info(f"Returning {len(pending_items)} pending items")
        return pending_items
    except Exception as e:
        logger.error(f"Pending items error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get pending items: {str(e)}")

@app.post("/api/quiz/answer")
async def submit_answer(
    answer: QuizAnswer,
    current_user: str = Depends(get_current_user)
):
    try:
        logger.info(f"Submitting answer for node {answer.node_id}, correct: {answer.correct}")
        
        # Get the node by element_id
        node_result = src.driver.execute_query(
            "MATCH (n) WHERE elementId(n) = $node_id RETURN n",
            node_id=answer.node_id
        )
        
        if not node_result.records:
            logger.error(f"Node not found: {answer.node_id}")
            raise HTTPException(status_code=404, detail="Node not found")
        
        node = node_result.records[0]["n"]
        
        # Process the answer using your existing logic
        src.check_answer(node, answer.correct)
        logger.info("Answer processed successfully")
        
        return {"message": "Answer recorded successfully"}
    except Exception as e:
        logger.error(f"Quiz answer error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

# Debug endpoint to see all available routes
@app.get("/api/debug/routes")
async def debug_routes():
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
async def debug_log():
    logger.info("Debug log test - INFO level")
    logger.warning("Debug log test - WARNING level")
    logger.error("Debug log test - ERROR level")
    return {"message": "Check console and ainki.log file for logs"}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return HTTPException(
        status_code=500, 
        detail=f"Internal server error: {str(exc)}"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
