import logging
import os
import tempfile
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List

import aiofiles
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from mnemosyne.evidence.store import EvidenceStore
from mnemosyne.graph.manager import GraphIngestionManager
from mnemosyne.graph.memgraph_client import MemgraphClient

logger = logging.getLogger(__name__)


# --- App State Management ---
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Setup
    logger.info("Initializing Mnemosyne API...")

    # Init DB clients
    memgraph_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    memgraph_user = os.getenv("NEO4J_USER", "")
    memgraph_password = os.getenv("NEO4J_PASSWORD", "")

    memgraph_client = MemgraphClient(
        uri=memgraph_uri, user=memgraph_user, password=memgraph_password
    )
    try:
        await memgraph_client.connect()
        await memgraph_client.initialize()
    except Exception as e:
        logger.error(f"Failed to connect to Memgraph during startup: {e}")
        # In a real app we might crash here. For development we log.

    evidence_store = EvidenceStore()
    await evidence_store.initialize()

    manager = GraphIngestionManager(memgraph_client, evidence_store)

    # Store on app state
    app.state.memgraph = memgraph_client
    app.state.evidence_store = evidence_store
    app.state.manager = manager

    yield  # App is running

    # Teardown
    logger.info("Shutting down Mnemosyne API...")
    await memgraph_client.close()


app = FastAPI(
    title="Mnemosyne Knowledge Graph API",
    description="API for ingesting files and querying the entity graph.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/ingest")
async def ingest_file(file: UploadFile = File(...)) -> Dict[str, Any]:  # noqa: B008
    """
    Ingest a file into the knowledge graph.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    manager: GraphIngestionManager = app.state.manager

    # Save the uploaded file to a temporary location
    try:
        fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1])
        os.close(fd)  # Close the C-level file descriptor immediately

        # Stream chunks to temp file
        async with aiofiles.open(temp_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                await f.write(chunk)

        # Process the file via our manager
        result = await manager.process_file(temp_path)

        return result

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        # Cleanup temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/api/search")
async def search_graph(q: str) -> List[Dict[str, Any]]:
    """
    Search for entities in the graph by a query string.
    """
    if not q or not q.strip():
        return []

    memgraph: MemgraphClient = app.state.memgraph

    try:
        results = await memgraph.search_entities(q.strip())
        return results
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
