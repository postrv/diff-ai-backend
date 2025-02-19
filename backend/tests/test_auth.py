# backend/tests/test_auth.py
from fastapi.testclient import TestClient
import pytest
from jose import jwt

from backend.app.main import app
from backend.app.config import settings


def test_login_success(client):
    """Test successful login and token generation."""
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Verify token is valid JWT
    payload = jwt.decode(
        data["access_token"],
        settings.secret_key,
        algorithms=[settings.algorithm]
    )
    assert payload["sub"] == "testuser"


def test_login_failure(client):
    """Test login with invalid credentials."""
    response = client.post(
        "/auth/login",
        data={"username": "wronguser", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()


def test_protected_route(client):
    """Test accessing a protected route with and without valid token."""
    # First get a valid token
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpassword"}
    )
    token = response.json()["access_token"]

    # Test with valid token
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

    # Test with invalid token
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401