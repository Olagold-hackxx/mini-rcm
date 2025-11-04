"""Tests for authentication API endpoints."""
import pytest
from fastapi import status


class TestAuthAPI:
    """Test authentication endpoints."""
    
    def test_signup_success(self, client):
        """Test successful user signup."""
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "user" in response.json()
        assert response.json()["user"]["username"] == "newuser"
    
    def test_signup_duplicate_username(self, client, test_user):
        """Test signup with duplicate username fails."""
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "username": "testuser",
                "email": "different@example.com",
                "password": "password123",
                "full_name": "Test User",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password fails."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "wrongpass"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user fails."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent", "password": "password123"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user(self, authenticated_client, test_user):
        """Test getting current user info."""
        response = authenticated_client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == "testuser"
        assert response.json()["email"] == "test@example.com"
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without auth fails."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

