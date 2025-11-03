"""Ingestion stage: Parse and load claims file."""
from typing import List, Dict, Any
import pandas as pd
from pipeline.stages.base_stage import BaseStage
from pipeline.parsers.claims_parser import ClaimsParser
from utils.logger import get_logger

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
        # Map common column name variations (more comprehensive)
        column_mapping = {
            "claim_id": ["claim_id", "claimid", "claim id", "id", "claimid", "claim_number"],
            "encounter_type": ["encounter_type", "encountertype", "encounter type", "encounter", "type"],
            "service_date": ["service_date", "servicedate", "service date", "date", "service date", "date_of_service"],
            "national_id": ["national_id", "nationalid", "national id", "national_id", "patient_id"],
            "member_id": ["member_id", "memberid", "member id", "member", "member_number"],
            "facility_id": ["facility_id", "facilityid", "facility id", "facility", "provider_id"],
            "unique_id": ["unique_id", "uniqueid", "unique id", "unique_identifier"],
            "diagnosis_codes": ["diagnosis_codes", "diagnosiscodes", "diagnosis codes", "diagnosis", "icd_codes"],
            "service_code": ["service_code", "servicecode", "service code", "service", "cpt_code", "procedure_code"],
            "paid_amount_aed": ["paid_amount_aed", "paidamount", "paid amount", "amount", "paid_amount", "paid_amount_aed", "amount_aed", "total_amount"],
            "approval_number": ["approval_number", "approvalnumber", "approval number", "approval", "authorization_number"],
        }
        
        # Normalize column names: strip, lower, replace spaces with underscores
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("-", "_")
        
        # Rename columns based on mapping
        for target_col, variations in column_mapping.items():
            for col in df.columns:
                if col in variations:
                    df.rename(columns={col: target_col}, inplace=True)
                    break
        
        logger.info(f"Normalized columns: {df.columns.tolist()}")
        
        # Convert service_date to datetime if present
        if "service_date" in df.columns:
            df["service_date"] = pd.to_datetime(
                df["service_date"], errors="coerce"
            )
        
        # Convert paid_amount_aed to numeric if present
        if "paid_amount_aed" in df.columns:
            df["paid_amount_aed"] = pd.to_numeric(df["paid_amount_aed"], errors="coerce")
        
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

