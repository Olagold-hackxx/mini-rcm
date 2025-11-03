"""Data quality stage: Schema and format validation."""
from typing import List, Dict, Any
import pandas as pd
from pipeline.stages.base_stage import BaseStage
from utils.logger import get_logger

logger = get_logger(__name__)


class DataQualityStage(BaseStage):
    """Stage 2: Validate data quality and schema compliance."""

    REQUIRED_FIELDS = []  # claim_id is auto-generated if missing
    REQUIRED_FIELDS_OPTIONAL = [
        "encounter_type",
        "service_date",
        "national_id",
        "member_id",
        "facility_id",
        "service_code",
        "paid_amount_aed",
    ]

    async def execute(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Execute data quality validation.
        
        Args:
            df: DataFrame with claims data
            
        Returns:
            List of claim dictionaries with data quality errors
        """
        self._log_stage_start("Data Quality")
        
        claims = df.to_dict("records")
        validated_claims = []
        
        for claim in claims:
            errors = self._validate_claim(claim)
            claim["data_quality_errors"] = errors
            validated_claims.append(claim)
        
        error_count = sum(
            1 for c in validated_claims if len(c["data_quality_errors"]) > 0
        )
        logger.info(f"Data quality: {error_count} claims with errors")
        
        self._log_stage_complete("Data Quality", len(validated_claims))
        return validated_claims

    def _validate_claim(self, claim: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate individual claim for data quality."""
        errors = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if not claim.get(field) or pd.isna(claim.get(field)):
                errors.append({
                    "type": "Data Quality Error",
                    "field": field,
                    "detail": f"Required field '{field}' is missing or empty",
                    "severity": "critical",
                })
        
        # Validate claim_id format
        if claim.get("claim_id"):
            claim_id = str(claim["claim_id"]).strip()
            if len(claim_id) == 0:
                errors.append({
                    "type": "Data Quality Error",
                    "field": "claim_id",
                    "detail": "Claim ID cannot be empty",
                    "severity": "critical",
                })
        
        # Validate numeric fields
        if claim.get("paid_amount_aed"):
            try:
                amount = float(claim["paid_amount_aed"])
                if amount < 0:
                    errors.append({
                        "type": "Data Quality Error",
                        "field": "paid_amount_aed",
                        "detail": "Paid amount cannot be negative",
                        "severity": "warning",
                    })
            except (ValueError, TypeError):
                errors.append({
                    "type": "Data Quality Error",
                    "field": "paid_amount_aed",
                    "detail": "Paid amount must be a valid number",
                    "severity": "error",
                })
        
        # Validate encounter_type values
        if claim.get("encounter_type"):
            encounter = str(claim["encounter_type"]).upper().strip()
            if encounter not in ["INPATIENT", "OUTPATIENT", ""]:
                errors.append({
                    "type": "Data Quality Error",
                    "field": "encounter_type",
                    "detail": f"Invalid encounter type: {encounter}. Must be INPATIENT or OUTPATIENT",
                    "severity": "warning",
                })
        
        return errors

