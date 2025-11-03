"""Pipeline orchestrator for claims validation."""
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

from models.database import ClaimMaster, ValidationMetrics
from pipeline.stages.ingestion import IngestionStage
from pipeline.stages.data_quality import DataQualityStage
from pipeline.stages.static_validation import StaticValidationStage
from pipeline.stages.llm_validation import LLMValidationStage
from utils.logger import get_logger

logger = get_logger(__name__)


class PipelineOrchestrator:
    """Orchestrates the complete validation pipeline."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.batch_id = self._generate_batch_id()
        
        # Initialize pipeline stages
        self.ingestion_stage = IngestionStage()
        self.data_quality_stage = DataQualityStage()
        self.static_validation_stage = StaticValidationStage(tenant_id)
        self.llm_validation_stage = LLMValidationStage(tenant_id)

    def _generate_batch_id(self) -> str:
        """Generate unique batch ID for tracking."""
        return f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    async def process_claims_file(
        self, file_path: str, uploaded_by: str
    ) -> Dict[str, Any]:
        """Main entry point for processing a claims file."""
        start_time = datetime.utcnow()
        logger.info(
            f"Starting pipeline for tenant {self.tenant_id}, batch {self.batch_id}"
        )
        
        try:
            # STAGE 1: INGESTION
            logger.info("Stage 1: Ingestion")
            claims_df = await self.ingestion_stage.execute(file_path)
            logger.info(f"Loaded {len(claims_df)} claims")
            
            # Ensure claim_id column exists and generate IDs for all rows
            claims_df = self._ensure_claim_ids(claims_df)
            
            # Insert raw claims into master table
            await self._insert_raw_claims(claims_df, uploaded_by)
            
            # STAGE 2: DATA QUALITY VALIDATION
            logger.info("Stage 2: Data Quality Validation")
            claims_with_dq = await self.data_quality_stage.execute(claims_df)
            
            # STAGE 3: STATIC RULES VALIDATION
            logger.info("Stage 3: Static Rules Validation")
            claims_with_static = await self.static_validation_stage.execute(
                claims_with_dq
            )
            
            # STAGE 4: LLM VALIDATION (Conditional)
            logger.info("Stage 4: LLM Validation")
            claims_final = await self.llm_validation_stage.execute(
                claims_with_static, claims_with_static
                )
            
            # STAGE 5: UPDATE MASTER TABLE
            logger.info("Stage 5: Updating Master Table")
            await self._update_master_table(claims_final)
            
            # STAGE 6: GENERATE ANALYTICS
            logger.info("Stage 6: Generating Analytics")
            metrics = await self._generate_metrics(claims_final)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Pipeline completed in {duration:.2f}s")
            
            return {
                "status": "success",
                "batch_id": self.batch_id,
                "total_claims": len(claims_df),
                "validated": metrics["validated_claims"],
                "not_validated": metrics["not_validated_claims"],
                "processing_time_seconds": duration,
                "metrics": metrics,
            }
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            raise

 

    def _ensure_claim_ids(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure claim_id exists for all rows. Generate unique IDs for missing/empty values.
        Also check database for existing claim_ids and append batch_id to make them unique.
        
        Args:
            df: DataFrame with claims data
            
        Returns:
            DataFrame with claim_id column populated for all rows
        """
        # Ensure claim_id column exists
        if "claim_id" not in df.columns:
            df["claim_id"] = None
        
        # Generate claim_ids for all rows that need them    
        for idx in df.index:
            raw_claim_id = df.loc[idx, "claim_id"]
            
            # Check if claim_id is missing or empty
            if pd.isna(raw_claim_id) or not str(raw_claim_id).strip():
                # Generate unique claim_id using batch_id and row index
                generated_id = f"{self.batch_id}_{idx}"
                df.loc[idx, "claim_id"] = generated_id
            else:
                # Clean up existing claim_id (strip whitespace)
                df.loc[idx, "claim_id"] = str(raw_claim_id).strip()
        
        # Handle any duplicates within the current file by appending index
        seen_ids = {}
        for idx in df.index:
            claim_id = df.loc[idx, "claim_id"]
            if claim_id in seen_ids:
                # Duplicate found within file, append index to make it unique
                df.loc[idx, "claim_id"] = f"{claim_id}_{idx}"
            seen_ids[df.loc[idx, "claim_id"]] = idx
        
        # Check database for existing claim_ids and append batch_id to make them unique
        # This prevents unique constraint violations when re-uploading files
        existing_claims = (
            self.db.query(ClaimMaster.claim_id)
            .filter(
                ClaimMaster.claim_id.in_(list(seen_ids.keys())),
                ClaimMaster.tenant_id == self.tenant_id
            )
            .all()
        )
        existing_claim_ids = {c.claim_id for c in existing_claims}
        
        if existing_claim_ids:
            # Append batch_id to claims that already exist in database
            for idx in df.index:
                claim_id = df.loc[idx, "claim_id"]
                if claim_id in existing_claim_ids:
                    # Claim ID already exists, append batch_id to make it unique
                    df.loc[idx, "claim_id"] = f"{claim_id}_{self.batch_id}"
                    logger.info(f"Claim ID {claim_id} already exists, renamed to {df.loc[idx, 'claim_id']}")
        
        logger.info(f"Generated claim_ids for {len(df)} claims")
        return df

    async def _insert_raw_claims(self, df: pd.DataFrame, uploaded_by: str):
        """
        Insert raw claims into master table.
        All claims should already have claim_id generated by _ensure_claim_ids.
        """
        claims = []
        
        for idx, row in df.iterrows():
            # claim_id should already be generated and validated by _ensure_claim_ids
            claim_id = str(row.get("claim_id", "")).strip()
            
            if not claim_id:
                # Fallback: generate if somehow still missing (shouldn't happen)
                claim_id = f"{self.batch_id}_{idx}"
                logger.warning(f"Had to generate claim_id for row {idx} in _insert_raw_claims")
            
            # Extract encounter_type using direct column access
            encounter_type = None
            if "encounter_type" in df.columns:
                encounter_type_val = row["encounter_type"] if "encounter_type" in row.index else None
                if pd.notna(encounter_type_val):
                    encounter_type_str = str(encounter_type_val).strip()
                    if encounter_type_str.lower() not in ['', 'nan', 'none', 'null']:
                        encounter_type = encounter_type_str
            
            # Extract service_date - already converted to datetime in ingestion stage
            service_date = None
            if "service_date" in df.columns:
                service_date_val = row["service_date"] if "service_date" in row.index else None
                if pd.notna(service_date_val):
                    service_date = service_date_val
            
            # Extract paid_amount_aed - already converted to numeric in ingestion stage
            paid_amount = None
            if "paid_amount_aed" in df.columns:
                paid_amount_val = row["paid_amount_aed"] if "paid_amount_aed" in row.index else None
                if pd.notna(paid_amount_val):
                    try:
                        paid_amount = float(paid_amount_val)
                    except (ValueError, TypeError):
                        paid_amount = None
            
            # Extract other fields using direct indexing
            national_id = row["national_id"] if "national_id" in row.index and pd.notna(row["national_id"]) else None
            if national_id:
                national_id = str(national_id).strip()
            
            member_id = row["member_id"] if "member_id" in row.index and pd.notna(row["member_id"]) else None
            if member_id:
                member_id = str(member_id).strip()
            
            facility_id = row["facility_id"] if "facility_id" in row.index and pd.notna(row["facility_id"]) else None
            if facility_id:
                facility_id = str(facility_id).strip()
            
            unique_id = row["unique_id"] if "unique_id" in row.index and pd.notna(row["unique_id"]) else None
            if unique_id:
                unique_id = str(unique_id).strip()
            
            diagnosis_codes = []
            if "diagnosis_codes" in row.index:
                val = row["diagnosis_codes"]
                if isinstance(val, list):
                    diagnosis_codes = val
                elif pd.notna(val):
                    if isinstance(val, str):
                        diagnosis_codes = [c.strip() for c in val.replace(",", " ").split() if c.strip()]
                    else:
                        diagnosis_codes = [str(val)]
            
            service_code = row["service_code"] if "service_code" in row.index and pd.notna(row["service_code"]) else None
            if service_code:
                service_code = str(service_code).strip()
            
            approval_number = row["approval_number"] if "approval_number" in row.index and pd.notna(row["approval_number"]) else None
            if approval_number:
                approval_number = str(approval_number).strip()
            
            claim = ClaimMaster(
                claim_id=claim_id,
                encounter_type=encounter_type,
                service_date=service_date,
                national_id=national_id,
                member_id=member_id,
                facility_id=facility_id,
                unique_id=unique_id,
                diagnosis_codes=diagnosis_codes,
                service_code=service_code,
                paid_amount_aed=paid_amount,
                approval_number=approval_number,
                tenant_id=self.tenant_id,
                batch_id=self.batch_id,
                uploaded_by=uploaded_by,
                status="Processing",
            )
            claims.append(claim)
        
        self.db.bulk_save_objects(claims)
        self.db.commit()
        logger.info(f"Inserted {len(claims)} raw claims")

    async def _update_master_table(self, claims: List[Dict]):
        """Update master table with validation results."""
        for claim_data in claims:
            claim = (
                self.db.query(ClaimMaster)
                .filter(
                    ClaimMaster.claim_id == claim_data["claim_id"],
                    ClaimMaster.tenant_id == self.tenant_id,
                )
                .first()
            )
            
            if claim:
                claim.status = claim_data.get("status", "Processing")
                claim.error_type = claim_data.get("error_type", "Unknown")
                claim.error_explanation = claim_data.get("error_explanation")
                claim.recommended_action = claim_data.get("recommended_action")
                claim.technical_errors = claim_data.get("technical_errors", [])
                claim.medical_errors = claim_data.get("medical_errors", [])
                claim.data_quality_errors = claim_data.get("data_quality_errors", [])
                claim.llm_evaluated = claim_data.get("llm_evaluated", False)
                claim.llm_confidence_score = claim_data.get("llm_confidence_score")
                claim.llm_explanation = claim_data.get("llm_explanation")
                claim.llm_retrieved_rules = claim_data.get("llm_retrieved_rules")
                claim.processed_at = datetime.utcnow()
        
        self.db.commit()
        logger.info(f"Updated {len(claims)} claims in master table")

    async def _generate_metrics(self, claims: List[Dict]) -> Dict[str, Any]:
        """Generate analytics metrics."""
        metrics = {
            "total_claims": len(claims),
            "validated_claims": sum(1 for c in claims if c["status"] == "Validated"),
            "not_validated_claims": sum(
                1 for c in claims if c["status"] == "Not validated"
            ),
            "no_error_count": sum(1 for c in claims if c["error_type"] == "No error"),
            "technical_error_count": sum(
                1 for c in claims if "Technical" in c.get("error_type", "")
            ),
            "medical_error_count": sum(
                1 for c in claims if "Medical" in c.get("error_type", "")
            ),
            "both_errors_count": sum(1 for c in claims if c["error_type"] == "Both"),
            "total_paid_amount": sum(
                float(c.get("paid_amount_aed", 0)) for c in claims
            ),
            "validated_amount": sum(
                float(c.get("paid_amount_aed", 0))
                for c in claims
                if c["status"] == "Validated"
            ),
            "rejected_amount": sum(
                float(c.get("paid_amount_aed", 0))
                for c in claims
                if c["status"] == "Not validated"
            ),
        }
        
        # Store metrics
        metric_record = ValidationMetrics(
            tenant_id=self.tenant_id,
            batch_id=self.batch_id,
            **metrics,
        )
        self.db.add(metric_record)
        self.db.commit()
        
        return metrics

