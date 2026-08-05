import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from mnemosyne.api.main import app

# Set an environment variable to use a test sqlite db
os.environ["MNEMOSYNE_EVIDENCE_DIR"] = tempfile.mkdtemp()


@pytest.fixture
def client():
    # TestClient automatically triggers the lifespan context manager
    with TestClient(app) as test_client:
        yield test_client


def test_ingest_and_search(client: TestClient):
    # 1. Test /api/ingest
    test_content = b"The new headquarters of Acme Corp will be in London."

    # We must mock the fact that Memgraph might be offline for integration tests in CI.
    # Let's try a simple query to see if it's alive.
    import asyncio

    try:
        asyncio.run(app.state.memgraph.execute_query("RETURN 1"))
    except Exception:
        pytest.skip("Memgraph is not connected, skipping API integration test.")

    # Clear graph before test
    asyncio.run(app.state.memgraph.execute_query("MATCH (n) DETACH DELETE n"))

    files = {"file": ("test_doc.txt", test_content, "text/plain")}

    response = client.post("/api/ingest", files=files)
    assert response.status_code == 200

    data = response.json()
    assert "evidence_hash" in data
    assert data["mime_type"] == "text/plain"
    assert data["entity_count"] >= 2  # Acme Corp, London

    # 2. Test /api/search
    search_response = client.get("/api/search", params={"q": "acme"})
    assert search_response.status_code == 200

    search_data = search_response.json()
    assert len(search_data) >= 1

    entity = search_data[0]
    assert "acme" in entity["name"].lower()
    assert data["evidence_hash"] in entity["evidence_hashes"]

    # Cleanup
    asyncio.run(app.state.memgraph.execute_query("MATCH (n) DETACH DELETE n"))
