import pytest
from fastapi.testclient import TestClient
from mnemosyne.api.main import app

client = TestClient(app)

def test_login_rate_limiting():
    # Attempt 5 logins
    for _ in range(5):
        response = client.post("/token", json={"username": "wrong", "password": "123"})
        # The first 5 should be 401 Unauthorized (because of wrong password, but not rate limited)
        assert response.status_code == 401
        
    # The 6th attempt should be 429 Too Many Requests
    response = client.post("/token", json={"username": "wrong", "password": "123"})
    assert response.status_code == 429

def test_successful_login():
    from mnemosyne.api.main import limiter
    limiter._storage.reset()
    
    response = client.post("/token", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    assert "access_token" in response.json()
