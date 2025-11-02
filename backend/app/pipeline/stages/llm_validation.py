"""LLM validation stage: Advanced reasoning and explanations."""
from typing import List, Dict, Any
from app.pipeline.stages.base_stage import BaseStage
from app.llm.evaluator import LLMEvaluator
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMValidationStage(BaseStage):
    """Stage 4: LLM-based validation for enhanced explanations."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.evaluator = LLMEvaluator(tenant_id)

    async def execute(
        self, claims_needing_llm: List[Dict], all_claims: List[Dict]
    ) -> List[Dict]:
        """
        Execute LLM validation on claims with errors.
        
        Args:
            claims_needing_llm: Claims that need LLM evaluation
            all_claims: All claims (to update in place)
            
        Returns:
            Updated all_claims list with LLM results
        """
        if not claims_needing_llm:
            logger.info("No claims require LLM evaluation")
            return all_claims
        
        self._log_stage_start("LLM Validation")
        
        # Create lookup for fast updates
        claims_dict = {c["claim_id"]: c for c in all_claims}
        
        # Process claims with LLM
        for claim in claims_needing_llm:
            try:
                llm_result = await self.evaluator.evaluate_claim(claim)
                
                # Update claim with LLM results
                claim_id = claim["claim_id"]
                if claim_id in claims_dict:
                    claims_dict[claim_id].update({
                        "llm_evaluated": True,
                        "llm_confidence_score": llm_result.get("confidence_score"),
                        "llm_explanation": llm_result.get("explanation"),
                        "llm_retrieved_rules": llm_result.get("retrieved_rules"),
                        "error_explanation": llm_result.get("enhanced_explanation"),
                        "recommended_action": llm_result.get("recommended_action"),
                    })
            except Exception as e:
                logger.error(f"LLM evaluation failed for claim {claim.get('claim_id')}: {e}")
                # Continue processing other claims
        
        processed_count = len(claims_needing_llm)
        logger.info(f"LLM validation completed for {processed_count} claims")
        self._log_stage_complete("LLM Validation", processed_count)
        
        return all_claims

