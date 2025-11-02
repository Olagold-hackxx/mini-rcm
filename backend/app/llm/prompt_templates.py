"""Prompt templates for LLM evaluation."""
from typing import List, Dict, Any


def get_validation_prompt(claim: Dict[str, Any], retrieved_rules: List[Dict]) -> str:
    """
    Generate prompt for LLM validation.
    
    Args:
        claim: Claim dictionary
        retrieved_rules: Relevant rules retrieved via RAG
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""You are a medical claims validation expert. Analyze the following claim and provide a detailed explanation of validation errors.

Claim Details:
- Claim ID: {claim.get('claim_id', 'N/A')}
- Encounter Type: {claim.get('encounter_type', 'N/A')}
- Service Code: {claim.get('service_code', 'N/A')}
- Diagnosis Codes: {claim.get('diagnosis_codes', [])}
- Facility ID: {claim.get('facility_id', 'N/A')}
- Paid Amount: {claim.get('paid_amount_aed', 'N/A')} AED
- Approval Number: {claim.get('approval_number', 'N/A')}

Validation Errors Detected:
"""
    
    # Add technical errors
    technical_errors = claim.get('technical_errors', [])
    if technical_errors:
        prompt += "\nTechnical Errors:\n"
        for error in technical_errors:
            prompt += f"- {error.get('detail', '')}\n"
    
    # Add medical errors
    medical_errors = claim.get('medical_errors', [])
    if medical_errors:
        prompt += "\nMedical Errors:\n"
        for error in medical_errors:
            prompt += f"- {error.get('detail', '')}\n"
    
    # Add retrieved rules if available
    if retrieved_rules:
        prompt += "\nRelevant Rules:\n"
        for rule in retrieved_rules[:5]:  # Top 5 rules
            prompt += f"- {rule.get('content', '')[:200]}\n"
    
    prompt += """
Please provide:
1. A clear, bulleted explanation of all errors
2. The recommended action for the provider
3. A confidence score (0-1) for your evaluation

Format your response as:
EXPLANATION: [detailed explanation]
RECOMMENDATION: [actionable recommendation]
CONFIDENCE: [0.0-1.0]
"""
    
    return prompt

