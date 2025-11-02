"""Ingestion stage: Parse and load claims file."""
from typing import List, Dict, Any
import pandas as pd
from app.pipeline.stages.base_stage import BaseStage
from app.pipeline.parsers.claims_parser import ClaimsParser
from app.utils.logger import get_logger

logger = get_logger(__name__)


class IngestionStage(BaseStage):
    """Stage 1: Parse claims file and prepare for validation."""

    def __init__(self):
        self.parser = ClaimsParser()

    async def execute(self, file_path: str) -> pd.DataFrame:
        """
        Execute ingestion stage.
        
        Args:
            file_path: Path to claims file
            
        Returns:
            DataFrame with parsed claims
        """
        self._log_stage_start("Ingestion")
        
        df = self.parser.parse(file_path)
        
        # Basic column mapping and type conversion
        df = self._normalize_dataframe(df)
        
        self._log_stage_complete("Ingestion", len(df))
        return df

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names and data types."""
        # Map common column name variations
        column_mapping = {
            "claim_id": ["claim_id", "claimid", "claim_id", "id"],
            "encounter_type": ["encounter_type", "encountertype", "encounter"],
            "service_date": ["service_date", "servicedate", "date", "service_date"],
            "national_id": ["national_id", "nationalid", "national_id"],
            "member_id": ["member_id", "memberid", "member"],
            "facility_id": ["facility_id", "facilityid", "facility"],
            "unique_id": ["unique_id", "uniqueid"],
            "diagnosis_codes": ["diagnosis_codes", "diagnosiscodes", "diagnosis"],
            "service_code": ["service_code", "servicecode", "service"],
            "paid_amount_aed": ["paid_amount_aed", "paidamount", "amount", "paid_amount"],
            "approval_number": ["approval_number", "approvalnumber", "approval"],
        }
        
        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()
        
        # Convert service_date to datetime if present
        if "service_date" in df.columns:
            df["service_date"] = pd.to_datetime(
                df["service_date"], errors="coerce"
            )
        
        # Convert diagnosis_codes to list if it's a string
        if "diagnosis_codes" in df.columns:
            df["diagnosis_codes"] = df["diagnosis_codes"].apply(
                lambda x: self._parse_diagnosis_codes(x) if pd.notna(x) else []
            )
        
        return df

    def _parse_diagnosis_codes(self, value: Any) -> List[str]:
        """Parse diagnosis codes from string to list."""
        if isinstance(value, list):
            return value
        
        if isinstance(value, str):
            # Handle comma-separated or space-separated codes
            codes = [c.strip() for c in value.replace(",", " ").split()]
            return [c for c in codes if c]
        
        return []

