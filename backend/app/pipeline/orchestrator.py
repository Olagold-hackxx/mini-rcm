"""Pipeline orchestrator for claims validation."""
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

from app.models.database import ClaimMaster, ValidationMetrics
from app.pipeline.stages.ingestion import IngestionStage
from app.pipeline.stages.data_quality import DataQualityStage
from app.pipeline.stages.static_validation import StaticValidationStage
from app.pipeline.stages.llm_validation import LLMValidationStage
from app.utils.logger import get_logger

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
            claims_needing_llm = self._filter_claims_for_llm(claims_with_static)
            
            if claims_needing_llm:
                claims_final = await self.llm_validation_stage.execute(
                    claims_needing_llm, claims_with_static
                )
            else:
                claims_final = claims_with_static
            
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

    def _filter_claims_for_llm(self, claims: List[Dict]) -> List[Dict]:
        """Filter claims that need LLM evaluation."""
        return [
            claim
            for claim in claims
            if claim.get("error_type") not in ["No error", None]
        ]

    async def _insert_raw_claims(self, df: pd.DataFrame, uploaded_by: str):
        """Insert raw claims into master table."""
        claims = []
        for _, row in df.iterrows():
            claim = ClaimMaster(
                claim_id=str(row.get("claim_id", "")),
                encounter_type=row.get("encounter_type"),
                service_date=pd.to_datetime(row.get("service_date"), errors="coerce"),
                national_id=str(row.get("national_id", "")) if pd.notna(row.get("national_id")) else None,
                member_id=str(row.get("member_id", "")) if pd.notna(row.get("member_id")) else None,
                facility_id=str(row.get("facility_id", "")) if pd.notna(row.get("facility_id")) else None,
                unique_id=str(row.get("unique_id", "")) if pd.notna(row.get("unique_id")) else None,
                diagnosis_codes=row.get("diagnosis_codes", []),
                service_code=str(row.get("service_code", "")) if pd.notna(row.get("service_code")) else None,
                paid_amount_aed=float(row.get("paid_amount_aed", 0)) if pd.notna(row.get("paid_amount_aed")) else None,
                approval_number=str(row.get("approval_number", "")) if pd.notna(row.get("approval_number")) else None,
                tenant_id=self.tenant_id,
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
                claim.status = claim_data["status"]
                claim.error_type = claim_data["error_type"]
                claim.error_explanation = claim_data["error_explanation"]
                claim.recommended_action = claim_data["recommended_action"]
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

