"""Tests for rules management API endpoints."""
import pytest
import json
from pathlib import Path


class TestRulesAPI:
    """Test rules management endpoints."""
    
    def test_get_rules(self, authenticated_client):
        """Test getting current rules."""
        response = authenticated_client.get("/api/v1/rules")
        assert response.status_code == 200
        assert "technical" in response.json()
        assert "medical" in response.json()
    
    def test_get_technical_rules(self, authenticated_client):
        """Test getting technical rules only."""
        response = authenticated_client.get("/api/v1/rules?rule_type=technical")
        assert response.status_code == 200
        assert "technical" in response.json()
    
    def test_update_rules(self, authenticated_client):
        """Test updating rules."""
        new_rules = {
            "services_requiring_approval": ["SRV1001"],
            "diagnoses_requiring_approval": ["E11.9"],
            "paid_amount_threshold": 1000.0,
            "unique_id_pattern": r"^[A-Z0-9-]{10,}$",
        }
        
        response = authenticated_client.put(
            "/api/v1/rules/technical",
            json=new_rules,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    
    def test_update_rules_invalid_type(self, authenticated_client):
        """Test updating rules with invalid type fails."""
        response = authenticated_client.put(
            "/api/v1/rules/invalid",
            json={},
        )
        assert response.status_code == 400
    
    def test_validate_rules(self, authenticated_client):
        """Test validating rules file."""
        response = authenticated_client.get("/api/v1/rules/technical/validate")
        assert response.status_code == 200
        assert "status" in response.json()
    
    def test_reload_rules(self, authenticated_client):
        """Test reloading rules."""
        response = authenticated_client.post("/api/v1/rules/technical/reload")
        assert response.status_code == 200
        assert response.json()["status"] == "success"

