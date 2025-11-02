"""FastAPI backend server for UAV Log Chatbot."""
import os
import uuid
from typing import Dict, Optional
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiofiles

from config import settings
from mavlink_parser import MAVLinkParser
from agent import FlightAnalysisAgent


# Pydantic models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    session_id: str
    message: str


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    session_id: str
    message: str
    timestamp: str


class SessionInfo(BaseModel):
    """Session information model."""
    session_id: str
    has_log: bool
    log_summary: Optional[Dict] = None
    created_at: str


# Initialize FastAPI app
app = FastAPI(
    title="UAV Log Chatbot API",
    description="Agentic chatbot for analyzing MAVLink flight logs",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (use Redis in production)
sessions: Dict[str, Dict] = {}
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def cleanup_old_sessions():
    """Remove sessions older than SESSION_TIMEOUT."""
    current_time = datetime.now()
    expired_sessions = []
    
    for session_id, session_data in sessions.items():
        created_at = session_data.get('created_at')
        if created_at:
            age = (current_time - created_at).total_seconds()
            if age > settings.session_timeout:
                expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        # Clean up files
        if 'file_path' in sessions[session_id]:
            try:
                os.remove(sessions[session_id]['file_path'])
            except:
                pass
        del sessions[session_id]


def get_or_create_session(session_id: Optional[str] = None) -> str:
    """Get existing session or create a new one."""
    cleanup_old_sessions()
    
    if session_id and session_id in sessions:
        return session_id
    
    # Create new session
    new_session_id = str(uuid.uuid4())
    sessions[new_session_id] = {
        'created_at': datetime.now(),
        'agent': FlightAnalysisAgent(new_session_id),
        'parser': None,
        'file_path': None
    }
    
    return new_session_id


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "UAV Log Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/upload",
            "chat": "/api/chat",
            "session": "/api/session/{session_id}",
            "reset": "/api/session/{session_id}/reset"
        }
    }


@app.post("/api/upload")
async def upload_log(file: UploadFile = File(...), session_id: Optional[str] = Form(None)):
    """
    Upload a MAVLink .bin log file.
    Creates a new session if session_id is not provided.
    """
    # Validate file type
    if not file.filename.endswith('.bin'):
        raise HTTPException(status_code=400, detail="Only .bin files are supported")
    
    # Check file size
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    temp_path = f"{UPLOAD_DIR}/temp_{uuid.uuid4()}.bin"
    
    try:
        async with aiofiles.open(temp_path, 'wb') as f:
            while chunk := await file.read(chunk_size):
                file_size += len(chunk)
                if file_size > settings.max_file_size_mb * 1024 * 1024:
                    os.remove(temp_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
                    )
                await f.write(chunk)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
    
    # Get or create session
    session_id = get_or_create_session(session_id)
    
    # Parse the log file
    try:
        parser = MAVLinkParser(temp_path)
        summary = parser.parse()
        
        # Store in session
        sessions[session_id]['parser'] = parser
        sessions[session_id]['file_path'] = temp_path
        sessions[session_id]['agent'].set_parser(parser)
        
        return {
            "session_id": session_id,
            "filename": file.filename,
            "file_size_bytes": file_size,
            "summary": summary,
            "message": "File uploaded and parsed successfully"
        }
    
    except Exception as e:
        os.remove(temp_path)
        raise HTTPException(status_code=400, detail=f"Failed to parse log file: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the agent about the uploaded log.
    Requires a valid session_id with an uploaded log.
    """
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a log file first.")
    
    session = sessions[request.session_id]
    agent = session['agent']
    
    try:
        response = agent.chat(request.message)
        
        return ChatResponse(
            session_id=request.session_id,
            message=response,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.get("/api/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get information about a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    has_log = session['parser'] is not None
    log_summary = None
    
    if has_log:
        log_summary = session['parser'].get_summary()
    
    return SessionInfo(
        session_id=session_id,
        has_log=has_log,
        log_summary=log_summary,
        created_at=session['created_at'].isoformat()
    )


@app.post("/api/session/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset the conversation history for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sessions[session_id]['agent'].reset_conversation()
    
    return {
        "session_id": session_id,
        "message": "Conversation history reset successfully"
    }


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and clean up associated files."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Clean up file
    if sessions[session_id]['file_path']:
        try:
            os.remove(sessions[session_id]['file_path'])
        except:
            pass
    
    del sessions[session_id]
    
    return {
        "session_id": session_id,
        "message": "Session deleted successfully"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_sessions": len(sessions),
        "llm_provider": "openai"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True
    )
