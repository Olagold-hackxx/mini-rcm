"""Tests for technical rules validator."""
import pytest
from pipeline.validators.technical_rules import TechnicalRulesEngine


class TestTechnicalRulesEngine:
    """Test technical rules validation."""
    
    @pytest.fixture
    def engine(self):
        """Create a technical rules engine."""
        return TechnicalRulesEngine("default")
    
    def test_service_approval_required_missing(self, engine):
        """Test that service requiring approval without approval number fails."""
        engine.rules = {
            "services_requiring_approval": ["SRV1001"],
            "diagnoses_requiring_approval": [],
            "paid_amount_threshold": 5000.0,
            "unique_id_pattern": r"^[A-Z0-9-]{10,}$",
        }
        
        claim = {
            "service_code": "SRV1001",
            "approval_number": None,
        }
        
        errors, _ = engine.validate(claim)
        assert len(errors) > 0
        assert any("requires prior approval" in e["detail"].lower() for e in errors)
    
    def test_service_approval_required_with_approval(self, engine):
        """Test that service requiring approval with approval number passes."""
        engine.rules = {
            "services_requiring_approval": ["SRV1001"],
            "diagnoses_requiring_approval": [],
            "paid_amount_threshold": 5000.0,
            "unique_id_pattern": r"^[A-Z0-9-]{10,}$",
        }
        
        claim = {
            "service_code": "SRV1001",
            "approval_number": "APRV001",
        }
        
        errors, _ = engine.validate(claim)
        assert len([e for e in errors if "approval" in e["detail"].lower()]) == 0
    
    def test_paid_amount_exceeds_threshold(self, engine):
        """Test that paid amount exceeding threshold fails."""
        engine.rules = {
            "services_requiring_approval": [],
            "diagnoses_requiring_approval": [],
            "paid_amount_threshold": 5000.0,
            "unique_id_pattern": r"^[A-Z0-9-]{10,}$",
        }
        
        claim = {
            "paid_amount_aed": 6000.0,
        }
        
        errors, _ = engine.validate(claim)
        assert len([e for e in errors if "threshold" in e["detail"].lower()]) > 0
    
    def test_unique_id_format_valid(self, engine):
        """Test valid unique ID format."""
        engine.rules = {
            "services_requiring_approval": [],
            "diagnoses_requiring_approval": [],
            "paid_amount_threshold": 5000.0,
            "unique_id_pattern": r"^[A-Z0-9-]{10,}$",
        }
        
        claim = {
            "unique_id": "ABCD-1234-EFGH",
        }
        
        errors, _ = engine.validate(claim)
        assert len([e for e in errors if "unique id" in e["detail"].lower()]) == 0
    
    def test_unique_id_segment_validation_first_segment(self, engine):
        """Test unique ID first segment matches National ID."""
        engine.rules = {
            "services_requiring_approval": [],
            "diagnoses_requiring_approval": [],
            "paid_amount_threshold": 5000.0,
            "unique_id_pattern": r"^[A-Z0-9-]{10,}$",
            "unique_id_validation": {"verify_segments": True},
        }
        
        claim = {
            "national_id": "NID001234",
            "member_id": "M001234",
            "facility_id": "FAC001234",
            "unique_id": "WRONG-M001-FAC0",  # First segment wrong
        }
        
        errors, _ = engine.validate(claim)
        assert len([e for e in errors if "first segment" in e["detail"].lower()]) > 0
    
    def test_unique_id_segment_validation_middle_segment(self, engine):
        """Test unique ID middle segment matches middle 4 of Member ID."""
        engine.rules = {
            "services_requiring_approval": [],
            "diagnoses_requiring_approval": [],
            "paid_amount_threshold": 5000.0,
            "unique_id_pattern": r"^[A-Z0-9-]{10,}$",
            "unique_id_validation": {"verify_segments": True},
        }
        
        claim = {
            "national_id": "NID001234",
            "member_id": "M0012345",  # 8 chars, middle 4 should be "0123"
            "facility_id": "FAC001234",
            "unique_id": "NID0-WRONG-FAC0",  # Middle segment wrong
        }
        
        errors, _ = engine.validate(claim)
        assert len([e for e in errors if "middle segment" in e["detail"].lower()]) > 0
    
    def test_unique_id_segment_validation_last_segment(self, engine):
        """Test unique ID last segment matches last 4 of Facility ID."""
        engine.rules = {
            "services_requiring_approval": [],
            "diagnoses_requiring_approval": [],
            "paid_amount_threshold": 5000.0,
            "unique_id_pattern": r"^[A-Z0-9-]{10,}$",
            "unique_id_validation": {"verify_segments": True},
        }
        
        claim = {
            "national_id": "NID001234",
            "member_id": "M001234",
            "facility_id": "FAC001234",  # Last 4 should be "1234"
            "unique_id": "NID0-M001-WRONG",  # Last segment wrong
        }
        
        errors, _ = engine.validate(claim)
        assert len([e for e in errors if "last segment" in e["detail"].lower()]) > 0
    
    def test_unique_id_segment_validation_all_correct(self, engine):
        """Test unique ID with all segments correct passes."""
        engine.rules = {
            "services_requiring_approval": [],
            "diagnoses_requiring_approval": [],
            "paid_amount_threshold": 5000.0,
            "unique_id_pattern": r"^[A-Z0-9-]{10,}$",
            "unique_id_validation": {"verify_segments": True},
        }
        
        claim = {
            "national_id": "NID001234",
            "member_id": "M0012345",  # Middle 4: "0123"
            "facility_id": "FAC001234",  # Last 4: "1234"
            "unique_id": "NID0-0123-1234",
        }
        
        errors, _ = engine.validate(claim)
        assert len([e for e in errors if "segment" in e["detail"].lower()]) == 0

