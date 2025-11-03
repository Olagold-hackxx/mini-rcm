"""LLM validation stage: Advanced reasoning and explanations."""
from typing import List, Dict, Any
from pipeline.stages.base_stage import BaseStage
from llm.evaluator import LLMEvaluator
from utils.logger import get_logger
import asyncio
import json


logger = get_logger(__name__)


class LLMValidationStage(BaseStage):
    """Stage 4: LLM-based validation for enhanced explanations."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.evaluator = LLMEvaluator(tenant_id)

    async def execute(self, claims_needing_llm: List[Dict], all_claims: List[Dict]) -> List[Dict]:
        if not claims_needing_llm:
            logger.info("No claims require LLM evaluation")
            return all_claims

        self._log_stage_start("LLM Validation")

        claims_dict = {c["claim_id"]: c for c in all_claims if "claim_id" in c}

        # Run all evaluations concurrently
        tasks = [self.evaluator.evaluate_claim(claim) for claim in claims_needing_llm]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for claim, result in zip(claims_needing_llm, results):
            claim_id = claim.get("claim_id")
            if not claim_id:
                logger.warning(f"Skipping claim without claim_id: {claim}")
                continue

            if isinstance(result, Exception):
                logger.error(f"LLM evaluation failed for claim {claim_id}: {result}")
                continue

            llm_result = result or {}
            logger.debug(f"LLM result for {claim_id}: {json.dumps(llm_result, indent=2)}")

            enhanced_explanation = llm_result.get("enhanced_explanation", "")
            confidence = llm_result.get("confidence_score", 0)
            llm_explanation = llm_result.get("explanation", "")
            executive_summary = llm_result.get("executive_summary", "")
            
            # Get explicit validation statuses from LLM response
            technical_validation_status = llm_result.get("technical_validation_status")
            medical_validation_status = llm_result.get("medical_validation_status")
            technical_rules_status = llm_result.get("technical_rules_status", [])
            medical_rules_status = llm_result.get("medical_rules_status", [])
            
            # Always use LLM explanation - it handles medical validation
            if enhanced_explanation:
                existing = claims_dict[claim_id].get("error_explanation", "")
                if existing:
                    claims_dict[claim_id]["error_explanation"] = (
                        f"{existing}\n\n--- LLM Medical Validation ---\n{enhanced_explanation}"
                    )
                else:
                    claims_dict[claim_id]["error_explanation"] = enhanced_explanation
            
            # Determine validation status using explicit LLM responses
            # If LLM provided explicit status, use it; otherwise fall back to keyword matching
            has_technical_errors = bool(claims_dict[claim_id].get("technical_errors"))
            has_data_quality_errors = bool(claims_dict[claim_id].get("data_quality_errors"))
            
            # Use explicit technical validation status from LLM if available
            if technical_validation_status:
                technical_passed = technical_validation_status.upper() == "PASS"
            else:
                # Fallback: use existing technical_errors
                technical_passed = not has_technical_errors
            
            # Use explicit medical validation status from LLM if available
            if medical_validation_status:
                medical_passed = medical_validation_status.upper() == "PASS"
            else:
                # Fallback: check for medical errors or keyword matching
                has_medical_errors_existing = bool(claims_dict[claim_id].get("medical_errors"))
                # Check LLM response text for medical validity indicators
                all_llm_text = " ".join([
                    executive_summary,
                    enhanced_explanation,
                    llm_explanation
                ]).lower()
                
                # Default to checking for violation indicators
                violation_indicators = [
                    "violates", "violation", "invalid", "not allowed", "not eligible",
                    "fails validation", "does not comply", "reject", "deny",
                    "missing approval", "requires approval", "approval number not found"
                ]
                valid_phrases = [
                    "no violations", "no medical rule violations", "claim is valid",
                    "medically valid", "passes all", "no violations found",
                    "no medical errors", "compliant with all"
                ]
                
                has_violation = any(indicator in all_llm_text for indicator in violation_indicators)
                has_valid_statement = any(phrase in all_llm_text for phrase in valid_phrases)
                
                medical_passed = not has_medical_errors_existing and (has_valid_statement or not has_violation)
            
            # Determine status based on explicit LLM validation results
            # Clear medical errors if medical validation passed
            if medical_passed:
                claims_dict[claim_id]["medical_errors"] = []
            
            # Update error_type and status based on explicit validation results
            if technical_passed and medical_passed and not has_data_quality_errors:
                # All validations passed - claim is fully validated
                claims_dict[claim_id]["status"] = "Validated"
                claims_dict[claim_id]["error_type"] = "No error"
                
                # Build comprehensive explanation with all passed rules
                explanation_parts = []
                
                # Add technical passed rules
                technical_passed_rules = claims_dict[claim_id].get("technical_passed_rules", [])
                if technical_passed_rules:
                    explanation_parts.append("TECHNICAL RULES VALIDATED:")
                    explanation_parts.append("=" * 50)
                    for rule in technical_passed_rules:
                        explanation_parts.append(f"✓ {rule.get('rule', 'Unknown Rule')} ({rule.get('rule_reference', 'N/A')})")
                        explanation_parts.append(f"  {rule.get('detail', '')}")
                    explanation_parts.append("")
                elif technical_rules_status:
                    explanation_parts.append("TECHNICAL RULES VALIDATED:")
                    explanation_parts.append("=" * 50)
                    for rule_status in technical_rules_status:
                        if rule_status.get("status") == "PASS":
                            explanation_parts.append(f"✓ {rule_status.get('rule', 'Unknown Rule')} - PASS")
                            explanation_parts.append(f"  {rule_status.get('reason', '')}")
                    explanation_parts.append("")
                
                # Add medical validation results from LLM
                explanation_parts.append("MEDICAL RULES VALIDATED:")
                explanation_parts.append("=" * 50)
                if medical_rules_status:
                    for rule_status in medical_rules_status:
                        if rule_status.get("status") == "PASS":
                            explanation_parts.append(f"✓ {rule_status.get('rule', 'Unknown Rule')} - PASS")
                            explanation_parts.append(f"  {rule_status.get('reason', '')}")
                    explanation_parts.append("")
                explanation_parts.append(enhanced_explanation or llm_explanation)
                
                claims_dict[claim_id]["error_explanation"] = "\n".join(explanation_parts)
                
            elif not technical_passed and medical_passed:
                # Technical validation failed but medical passed
                claims_dict[claim_id]["status"] = "Not validated"
                claims_dict[claim_id]["error_type"] = "Technical error"
                logger.info(f"Claim {claim_id}: Technical failed, Medical passed - error_type set to Technical error")
                
            elif technical_passed and not medical_passed:
                # Technical validation passed but medical failed
                # Create medical error entry if not exists
                if not claims_dict[claim_id].get("medical_errors"):
                    medical_error_detail = llm_explanation[:500].strip("*") if llm_explanation else enhanced_explanation[:500]
                    if medical_rules_status:
                        failed_rules = [rs for rs in medical_rules_status if rs.get("status") == "FAIL"]
                        if failed_rules:
                            medical_error_detail = "\n".join([
                                f"- {rule.get('rule')}: {rule.get('reason', '')}"
                                for rule in failed_rules
                            ])
                    
                    claims_dict[claim_id]["medical_errors"] = [{
                        "type": "Medical error",
                        "rule": "LLM Medical Validation",
                        "rule_reference": "LLM Analysis",
                        "detail": medical_error_detail,
                        "severity": "error",
                    }]
                
                claims_dict[claim_id]["status"] = "Not validated"
                claims_dict[claim_id]["error_type"] = "Medical error"
                logger.info(f"Claim {claim_id}: Technical passed, Medical failed - error_type set to Medical error")
                
            elif not technical_passed and not medical_passed:
                # Both validations failed
                # Create medical error entry if not exists
                if not claims_dict[claim_id].get("medical_errors"):
                    medical_error_detail = llm_explanation[:500].strip("*") if llm_explanation else enhanced_explanation[:500]
                    if medical_rules_status:
                        failed_rules = [rs for rs in medical_rules_status if rs.get("status") == "FAIL"]
                        if failed_rules:
                            medical_error_detail = "\n".join([
                                f"- {rule.get('rule')}: {rule.get('reason', '')}"
                                for rule in failed_rules
                            ])
                    
                    claims_dict[claim_id]["medical_errors"] = [{
                        "type": "Medical error",
                        "rule": "LLM Medical Validation",
                        "rule_reference": "LLM Analysis",
                        "detail": medical_error_detail,
                        "severity": "error",
                    }]
                
                claims_dict[claim_id]["status"] = "Not validated"
                claims_dict[claim_id]["error_type"] = "Both"
                logger.info(f"Claim {claim_id}: Both Technical and Medical failed - error_type set to Both")
            
            else:
                # Fallback: couldn't determine status definitively
                if "status" not in claims_dict[claim_id] or not claims_dict[claim_id].get("status"):
                    claims_dict[claim_id]["status"] = "Not validated"
                if "error_type" not in claims_dict[claim_id] or not claims_dict[claim_id].get("error_type"):
                    claims_dict[claim_id]["error_type"] = "Unknown"
                logger.warning(f"Claim {claim_id}: Could not definitively determine validation status")

            claims_dict[claim_id].update({
                "llm_evaluated": True,
                "llm_confidence_score": confidence,
                "llm_explanation": llm_explanation,
                "llm_retrieved_rules": llm_result.get("retrieved_rules", []),
                "recommended_action": llm_result.get("recommended_action")
                    or claims_dict[claim_id].get("recommended_action", ""),
            })

        logger.info(f"LLM validation completed for {len(claims_needing_llm)} claims")
        self._log_stage_complete("LLM Validation", len(claims_needing_llm))

        return list(claims_dict.values())

