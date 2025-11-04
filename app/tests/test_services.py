"""Tests for service layer."""
import pytest
from services.rule_config_service import RuleConfigService
from pathlib import Path
import json
import shutil


class TestRuleConfigService:
    """Test rule configuration service."""
    
    def test_get_technical_rules_default(self):
        """Test getting default technical rules."""
        rules = RuleConfigService.get_technical_rules("nonexistent_tenant")
        assert "services_requiring_approval" in rules
        assert "paid_amount_threshold" in rules
    
    def test_get_medical_rules_default(self):
        """Test getting default medical rules."""
        rules = RuleConfigService.get_medical_rules("nonexistent_tenant")
        assert "inpatient_services" in rules
        assert "outpatient_services" in rules
    
    def test_update_rules(self):
        """Test updating rules for a tenant."""
        tenant_id = "test_update_tenant"
        test_rules = {
            "services_requiring_approval": ["TEST001"],
            "paid_amount_threshold": 1000.0,
        }
        
        success = RuleConfigService.update_rules(tenant_id, "technical", test_rules)
        assert success is True
        
        # Verify rules were saved
        rules_path = Path(f"app/rules/{tenant_id}/technical_rules.json")
        assert rules_path.exists()
        
        with open(rules_path) as f:
            saved_rules = json.load(f)
            assert saved_rules["services_requiring_approval"] == ["TEST001"]
        
        # Cleanup
        RuleConfigService.invalidate_cache(tenant_id, "technical")
        if Path(f"app/rules/{tenant_id}").exists():
            shutil.rmtree(Path(f"app/rules/{tenant_id}"))
    
    def test_invalidate_cache(self):
        """Test cache invalidation."""
        RuleConfigService.invalidate_cache("default", "technical")
        # Should not raise exception
    
    def test_get_rules_path(self):
        """Test getting rules path."""
        path = RuleConfigService.get_rules_path("default", "technical")
        assert isinstance(path, Path)
        assert "default" in str(path)
        assert "technical" in str(path)

