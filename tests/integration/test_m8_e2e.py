import pytest
import os
from fastapi.testclient import TestClient
from mnemosyne.api.main import app

client = TestClient(app)

def test_m8_upload_and_graph():
    # 1. Create a dummy test file
    test_file_path = "test_upload.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test document with an entity named John Doe.")
        
    try:
        # 2. Upload it
        with open(test_file_path, "rb") as f:
            response = client.post("/api/v1/upload", files={"file": ("test_upload.txt", f, "text/plain")})
        
        assert response.status_code == 200
        assert response.json()["status"] == "started"
        assert response.json()["file"] == "test_upload.txt"
        
        # 3. Check graph endpoint
        graph_response = client.get("/api/v1/graph")
        assert graph_response.status_code == 200
        
        # 4. Check query endpoint
        query_response = client.post("/api/v1/query", json={"query": "Who is John Doe?"})
        assert query_response.status_code == 200
        assert "Generated report for" in query_response.json()["report"]
        
    finally:
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
