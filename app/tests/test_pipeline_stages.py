"""Tests for pipeline stages."""
import pytest
from pipeline.stages.ingestion import IngestionStage
from pipeline.stages.data_quality import DataQualityStage
from pipeline.stages.static_validation import StaticValidationStage


class TestIngestionStage:
    """Test ingestion stage."""
    
    @pytest.fixture
    def stage(self):
        """Create ingestion stage."""
        return IngestionStage()
    
    def test_ingest_csv(self, stage, sample_claims_file):
        """Test ingesting CSV file."""
        import asyncio
        result = asyncio.run(stage.execute(sample_claims_file))
        assert len(result) == 2
        assert "claim_id" in result.columns
        assert result.iloc[0]["service_code"] == "SRV2007"


class TestDataQualityStage:
    """Test data quality validation stage."""
    
    @pytest.fixture
    def stage(self):
        """Create data quality stage."""
        return DataQualityStage()
    
    def test_missing_required_fields(self, stage):
        """Test that missing required fields are flagged."""
        import pandas as pd
        import asyncio
        
        claims = pd.DataFrame({
            "claim_id": ["C001"],
            "service_code": [None],  # Missing required field
        })
        
        result = asyncio.run(stage.execute(claims))
        assert len(result) == 1
        assert result.iloc[0].get("data_quality_errors")


class TestStaticValidationStage:
    """Test static validation stage."""
    
    @pytest.fixture
    def stage(self):
        """Create static validation stage."""
        return StaticValidationStage("default")
    
    def test_technical_validation(self, stage):
        """Test technical rules validation."""
        import asyncio
        
        claims = [{
            "claim_id": "C001",
            "service_code": "SRV1001",
            "approval_number": None,
            "paid_amount_aed": 100.0,
            "unique_id": "ABCD-1234-EFGH",
        }]
        
        # Set up rules
        stage.technical_engine.rules = {
            "services_requiring_approval": ["SRV1001"],
            "diagnoses_requiring_approval": [],
            "paid_amount_threshold": 5000.0,
            "unique_id_pattern": r"^[A-Z0-9-]{10,}$",
        }
        
        result = asyncio.run(stage.execute(claims))
        assert len(result) == 1
        assert result[0]["status"] == "Not validated"
        assert len(result[0].get("technical_errors", [])) > 0

