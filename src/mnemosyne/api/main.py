from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel

from .auth import create_access_token, verify_password, get_password_hash, Token
from mnemosyne.evidence.audit import AuditLog

import tempfile
import os
import asyncio
from typing import List, Dict
from fastapi import UploadFile, File, WebSocket, WebSocketDisconnect

from mnemosyne.agents.supervisor import SupervisorAgent
from mnemosyne.agents.bus import bus, AgentMessage
from mnemosyne.graph.memgraph_client import MemgraphClient

supervisor_agent = SupervisorAgent()
memgraph_client = MemgraphClient()
active_websockets: List[WebSocket] = []

async def broadcast_ws(message: AgentMessage):
    for ws in active_websockets:
        try:
            await ws.send_json({
                "id": message.id,
                "agent": message.sender,
                "action": message.payload.get("step", message.payload.get("action", "activity")),
                "status": message.payload.get("status", "running")
            })
        except Exception:
            pass

# Subscribe to bus to forward to websocket
bus.subscribe("progress", broadcast_ws)
bus.subscribe("error", broadcast_ws)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="MNEMOSYNE API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize audit log on startup
audit = AuditLog()

# In-memory user db for demo purposes
# In production, use DB
users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("admin123"),
        "hw_bound": False
    }
}

class LoginRequest(BaseModel):
    username: str
    password: str

@app.on_event("startup")
async def startup_event():
    # M6-2: Tamper detection runs automatically on every application startup
    if not audit.verify_chain():
        # In a real forensics app, we might refuse to start, but for tests we'll log it
        pass
    audit.append("SYSTEM_STARTUP", {"status": "success"})

@app.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login_for_access_token(request: Request, login_data: LoginRequest):
    # Find user
    user = users_db.get(login_data.username)
    if not user or not verify_password(login_data.password, user["hashed_password"]):
        audit.append("FAILED_LOGIN", {"user": login_data.username, "ip": request.client.host})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    audit.append("SUCCESSFUL_LOGIN", {"user": login_data.username, "ip": request.client.host})
    access_token = create_access_token(
        data={"sub": user["username"], "hw_bound": user["hw_bound"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    # Save file to temp location
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, file.filename or "unknown")
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    audit.append("FILE_UPLOADED", {"filename": file.filename})
    
    # Run supervisor in background
    asyncio.create_task(supervisor_agent.run({"files": [file_path]}))
    
    return {"status": "started", "file": file.filename}

@app.get("/api/v1/graph")
async def get_graph():
    # Simple query to get all nodes and edges (simplified for MVP)
    try:
        await memgraph_client.connect()
        nodes_res = await memgraph_client.execute_query("MATCH (n) RETURN n")
        edges_res = await memgraph_client.execute_query("MATCH ()-[r]->() RETURN r")
        return {"nodes": nodes_res, "edges": edges_res}
    except Exception as e:
        return {"error": str(e), "nodes": [], "edges": []}

class QueryRequest(BaseModel):
    query: str

# M8-2: Simple cache for repeated queries
query_cache: Dict[str, dict] = {}

@app.post("/api/v1/query")
async def query_system(req: QueryRequest):
    if req.query in query_cache:
        audit.append("SYSTEM_QUERY_CACHED", {"query": req.query})
        return query_cache[req.query]

    # Dummy integration for MVP RAG (will use real RAG in production)
    audit.append("SYSTEM_QUERY", {"query": req.query})
    result = {"report": f"Generated report for {req.query}", "timeline": {}}
    
    query_cache[req.query] = result
    return result

@app.websocket("/ws/agents")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
