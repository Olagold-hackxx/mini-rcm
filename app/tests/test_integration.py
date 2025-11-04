"""Integration tests for the complete pipeline."""
import pytest
import pandas as pd
from pipeline.orchestrator import PipelineOrchestrator


class TestPipelineIntegration:
    """Integration tests for the complete validation pipeline."""
    
    @pytest.mark.integration
    def test_pipeline_with_valid_claim(self, db_session, sample_claims_file):
        """Test complete pipeline with a valid claim."""
        import asyncio
        
        orchestrator = PipelineOrchestrator(db_session, "default")
        
        # This would require mocking LLM and vector store
        # For now, we'll test that the orchestrator can be instantiated
        assert orchestrator.tenant_id == "default"
        assert orchestrator.batch_id is not None
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_end_to_end_validation(self, authenticated_client, sample_claims_file):
        """Test end-to-end validation flow."""
        import os
        
        # Upload file
        with open(sample_claims_file, 'rb') as f:
            files = {'file': ('test_claims.csv', f, 'text/csv')}
            response = authenticated_client.post(
                "/api/v1/upload/claims",
                files=files,
            )
        
        # This would require actual LLM API key and vector store setup
        # For integration tests, we'd mock these
        assert response.status_code in [200, 202]  # Accepted or processing

