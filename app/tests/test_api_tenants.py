"""Tests for tenant management API endpoints."""
import pytest
from pathlib import Path
import shutil


class TestTenantsAPI:
    """Test tenant management endpoints."""
    
    def test_get_current_tenant(self, authenticated_client):
        """Test getting current tenant info."""
        response = authenticated_client.get("/api/v1/tenants/current")
        assert response.status_code == 200
        assert "tenant_id" in response.json()
    
    def test_list_tenants(self, authenticated_client):
        """Test listing all tenants."""
        response = authenticated_client.get("/api/v1/tenants/list")
        assert response.status_code == 200
        assert "tenants" in response.json()
    
    def test_create_tenant(self, authenticated_client):
        """Test creating a new tenant."""
        response = authenticated_client.post(
            "/api/v1/tenants/create",
            json={
                "tenant_id": "test_tenant_123",
                "copy_from_default": True,
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
        # Cleanup
        tenant_dir = Path("app/rules/test_tenant_123")
        if tenant_dir.exists():
            shutil.rmtree(tenant_dir)
    
    def test_create_tenant_invalid_id(self, authenticated_client):
        """Test creating tenant with invalid ID format fails."""
        response = authenticated_client.post(
            "/api/v1/tenants/create",
            json={
                "tenant_id": "invalid tenant id!",
                "copy_from_default": True,
            },
        )
        assert response.status_code == 400
    
    def test_create_tenant_default_reserved(self, authenticated_client):
        """Test that 'default' tenant ID cannot be created."""
        response = authenticated_client.post(
            "/api/v1/tenants/create",
            json={
                "tenant_id": "default",
                "copy_from_default": True,
            },
        )
        assert response.status_code == 400

