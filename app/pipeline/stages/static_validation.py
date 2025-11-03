"""Static validation stage: Apply technical and medical rules."""
from typing import List, Dict, Any
from pipeline.stages.base_stage import BaseStage
from pipeline.validators.technical_rules import TechnicalRulesEngine
from pipeline.validators.medical_rules import MedicalRulesEngine
from utils.logger import get_logger

logger = get_logger(__name__)


class StaticValidationStage(BaseStage):
    """Stage 3: Apply deterministic rule-based validation."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.technical_engine = TechnicalRulesEngine(tenant_id)
        self.medical_engine = MedicalRulesEngine(tenant_id)

    async def execute(self, claims: List[Dict]) -> List[Dict]:
        """
        Validate each claim against static rules.
        
        Args:
            claims: List of claim dictionaries with data quality results
            
        Returns:
            List of claims with static validation results
        """
        self._log_stage_start("Static Validation")
        
        validated_claims = []
        
        for claim in claims:
            # Skip if already has data quality errors
            if claim.get("data_quality_errors"):
                claim["status"] = "Not validated"
                claim["error_type"] = "Technical error"
                validated_claims.append(claim)
                continue
            
            # Run technical validation (returns errors and passed_rules)
            technical_result = self.technical_engine.validate(claim)
            if isinstance(technical_result, tuple):
                technical_errors, technical_passed_rules = technical_result
            else:
                # Backward compatibility - if old format, treat as errors only
                technical_errors = technical_result
                technical_passed_rules = []
            
            # Skip medical validation - let LLM handle it
            # medical_errors = self.medical_engine.validate(claim)
            medical_errors = []  # Empty list - LLM will validate medical rules
            
            # Store passed technical rules
            claim["technical_passed_rules"] = technical_passed_rules
            
            # Aggregate results
            claim = self._aggregate_errors(claim, technical_errors, medical_errors)
            validated_claims.append(claim)
        
        logger.info(f"Static validation completed for {len(claims)} claims")
        self._log_stage_complete("Static Validation", len(validated_claims))
        return validated_claims

    def _aggregate_errors(
        self,
        claim: Dict,
        technical_errors: List[Dict],
        medical_errors: List[Dict],
    ) -> Dict:
        """Combine technical and medical errors into final validation result."""
        claim["technical_errors"] = technical_errors
        claim["medical_errors"] = medical_errors
        
        has_technical = len(technical_errors) > 0
        has_medical = len(medical_errors) > 0
        
        # Determine status
        if not has_technical and not has_medical:
            claim["status"] = "Validated"
            claim["error_type"] = "No error"
            claim["error_explanation"] = (
                "No errors detected. Claim passes all validation rules."
            )
            claim["recommended_action"] = "Approve claim for payment."
        else:
            claim["status"] = "Not validated"
            
            if has_technical and has_medical:
                claim["error_type"] = "Both"
            elif has_technical:
                claim["error_type"] = "Technical error"
            else:
                claim["error_type"] = "Medical error"
            
            # Generate basic explanation
            claim["error_explanation"] = self._format_error_explanation(
                technical_errors, medical_errors
            )
            claim["recommended_action"] = self._generate_basic_recommendation(
                technical_errors, medical_errors
            )
        
        return claim

    def _format_error_explanation(
        self, technical_errors: List[Dict], medical_errors: List[Dict]
    ) -> str:
        """Format errors as bulleted list."""
        explanation = []
        
        for error in technical_errors:
            explanation.append(f"• {error['detail']}")
        
        for error in medical_errors:
            explanation.append(f"• {error['detail']}")
        
        return "\n".join(explanation)

    def _generate_basic_recommendation(
        self, technical_errors: List[Dict], medical_errors: List[Dict]
    ) -> str:
        """Generate basic recommendation."""
        if technical_errors:
            return (
                "Obtain required prior approval and verify all ID formats "
                "before resubmission."
            )
        if medical_errors:
            return (
                "Review service-diagnosis alignment and facility eligibility "
                "before resubmission."
            )
        return "Review and correct all identified errors."

