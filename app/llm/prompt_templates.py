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
    # Determine if claim has errors
    has_errors = (
        len(claim.get("technical_errors", [])) > 0
        or len(claim.get("medical_errors", [])) > 0
        or len(claim.get("data_quality_errors", [])) > 0
    )

    prompt = f"""You are a senior medical claims validation expert with deep knowledge of healthcare billing, coding, and adjudication rules. Your task is to provide a comprehensive, detailed analysis of the following claim.

CLAIM INFORMATION:
==================
- Claim ID: {claim.get('claim_id', 'N/A')}
- Encounter Type: {claim.get('encounter_type', 'N/A')}
- Service Date: {claim.get('service_date', 'N/A')}
- Service Code: {claim.get('service_code', 'N/A')}
- Diagnosis Codes: {', '.join(map(str, claim.get('diagnosis_codes', []))) or 'N/A'}
- Facility ID: {claim.get('facility_id', 'N/A')}
- Member ID: {claim.get('member_id', 'N/A')}
- National ID: {claim.get('national_id', 'N/A')}
- Unique ID: {claim.get('unique_id', 'N/A')}
- Paid Amount: {claim.get('paid_amount_aed', 'N/A')} AED
- Approval Number: {claim.get('approval_number', 'N/A')}

CRITICAL: If the claim has an approval number listed above, it MUST be considered valid for approval requirements.
Do NOT flag as missing approval if an approval number is present in the claim data above.

"""

    # Add error details if present
    if has_errors:
        prompt += "VALIDATION ERRORS DETECTED:\n"
        prompt += "=" * 50 + "\n"

    technical_errors = claim.get("technical_errors", [])
    if technical_errors:
        prompt += "\nTECHNICAL ERRORS:\n"
        prompt += "IMPORTANT: If technical errors are listed below, TECHNICAL_VALIDATION must be FAIL.\n"
        prompt += (
            "Only mark TECHNICAL_VALIDATION as PASS if NO technical errors exist.\n\n"
        )
        for i, error in enumerate(technical_errors, 1):
            prompt += f"{i}. {error.get('rule', 'Unknown Rule')}\n"
            prompt += f"   Detail: {error.get('detail', '')}\n"
            prompt += f"   Reference: {error.get('rule_reference', 'N/A')}\n"
            prompt += f"   Severity: {error.get('severity', 'error')}\n\n"
    else:
        prompt += "\nTECHNICAL ERRORS: None detected.\n"
        prompt += "IMPORTANT: Since no technical errors are listed, TECHNICAL_VALIDATION must be PASS.\n\n"

    medical_errors = claim.get("medical_errors", [])
    if medical_errors:
        prompt += "\nEXISTING MEDICAL ERRORS:\n"
        prompt += "CRITICAL: If medical errors are listed below, MEDICAL_VALIDATION must be FAIL.\n"
        prompt += "Only mark MEDICAL_VALIDATION as PASS if NO medical errors exist.\n\n"
        prompt += "Note: You will perform medical validation below regardless of existing errors.\n"
        for i, error in enumerate(medical_errors, 1):
            prompt += f"{i}. {error.get('rule', 'Unknown Rule')}\n"
            prompt += f"   Detail: {error.get('detail', '')}\n\n"

    data_quality_errors = claim.get("data_quality_errors", [])
    if data_quality_errors:
        prompt += "\nDATA QUALITY ERRORS:\n"
        for i, error in enumerate(data_quality_errors, 1):
            prompt += f"{i}. {error.get('detail', '')}\n"
            prompt += f"   Field: {error.get('field', 'N/A')}\n"
            prompt += f"   Severity: {error.get('severity', 'error')}\n\n"
            prompt += "CRITICAL: If data quality errors are listed above, MEDICAL_VALIDATION must be FAIL.\n"
            prompt += "Only mark MEDICAL_VALIDATION as PASS if NO data quality errors exist.\n\n"
    else:
        prompt += "STATUS: No technical errors detected from static validation.\n\n"
        prompt += (
            "CRITICAL: You must perform medical rules validation for this claim.\n\n"
        )
        prompt += "IMPORTANT RESTRICTIONS:\n"
        prompt += "======================\n"
        prompt += "1. You MUST ONLY validate against the rules provided in the 'RELEVANT ADJUDICATION RULES' section below.\n"
        prompt += "2. DO NOT make assumptions or infer rules that are not explicitly stated in the retrieved rules.\n"
        prompt += "3. DO NOT flag violations based on general medical knowledge that is not in the provided rules.\n"
        prompt += "4. If a rule is not found in the retrieved rules, assume it does not apply to this claim.\n"
        prompt += "5. Only report violations that can be directly referenced to specific rules provided below.\n\n"
        prompt += "VALIDATION APPROACH:\n"
        prompt += "===================\n"
        prompt += "CRITICAL: You MUST check the following medical rules in this EXACT order:\n\n"
        prompt += "1. SERVICE-DIAGNOSIS REQUIREMENTS (MANDATORY CHECK):\n"
        prompt += "   - Check if the service code has a REQUIRED diagnosis code in the rules.\n"
        prompt += "   - If the service code requires a specific diagnosis, and the claim's diagnosis does NOT match, this is a FAILURE.\n"
        prompt += "   - Example: If rules say 'SRV2007 requires E11.9' but claim has 'SRV2007 with J45.909', this FAILS.\n"
        prompt += "   - If rules say 'SRV2006 requires J45.909' but claim has 'SRV2006 with E11.9', this FAILS.\n"
        prompt += "   - This is a CRITICAL medical rule violation - mark MEDICAL_VALIDATION as FAIL if mismatch found.\n\n"
        prompt += "2. SERVICE-ENCOUNTER TYPE ELIGIBILITY:\n"
        prompt += "   - Check if the service code is allowed for the encounter type (INPATIENT/OUTPATIENT).\n"
        prompt += "   - If rules specify which services are allowed for which encounter types, verify compliance.\n"
        prompt += "   - If service is not in the allowed list for the encounter type, this is a FAILURE.\n\n"
        prompt += "3. FACILITY-SERVICE ELIGIBILITY:\n"
        prompt += "   - Check if the facility type allows this service code.\n"
        prompt += "   - If rules specify which services are allowed at which facility types, verify compliance.\n"
        prompt += "   - If service is not in the allowed list for the facility type, this is a FAILURE.\n\n"
        prompt += "4. MUTUALLY EXCLUSIVE DIAGNOSES:\n"
        prompt += "   - Check if the claim has multiple diagnosis codes that are mutually exclusive.\n"
        prompt += "   - If rules specify mutually exclusive diagnoses and the claim has both, this is a FAILURE.\n\n"
        prompt += "5. APPROVAL REQUIREMENTS (CRITICAL CHECK):\n"
        prompt += (
            "   - Check if the SERVICE CODE requires approval according to the rules.\n"
        )
        prompt += "   - Check if any DIAGNOSIS CODE requires approval according to the rules.\n"
        prompt += "   - If EITHER the service OR diagnosis requires approval, then:\n"
        prompt += "     * Approval number MUST be present in the claim.\n"
        prompt += "     * If approval is required but approval number is MISSING, this is a FAILURE.\n"
        prompt += "     * If approval is required and approval number is PRESENT, this is a PASS.\n"
        prompt += "   - If NEITHER service nor diagnosis requires approval, approval number is optional (PASS).\n"
        prompt += "   - Example: If rules say 'SRV1001 requires approval' but claim has no approval number, this FAILS.\n"
        prompt += "   - Example: If rules say 'Diagnosis E11.9 requires approval' but claim has E11.9 with no approval, this FAILS.\n"
        prompt += "   - Example: If rules say 'SRV2007 does not require approval' and claim has no approval, this PASSES.\n\n"
        prompt += "IMPORTANT: If you find ANY violation in the above checks based on the provided rules, you MUST mark MEDICAL_VALIDATION as FAIL.\n"
        prompt += "Only mark MEDICAL_VALIDATION as PASS if ALL checks pass AND the claim complies with all provided rules.\n\n"

    # Add retrieved rules if available
    if retrieved_rules:
        prompt += "\nRELEVANT ADJUDICATION RULES:\n"
        prompt += "=" * 50 + "\n"
        prompt += "CRITICAL: You MUST ONLY use these rules for validation. Do NOT use any rules not listed here.\n\n"
        # Display more rules with more content to give LLM complete context
        # Show up to 50 rules with full content to ensure comprehensive coverage
        for i, rule in enumerate(
            retrieved_rules[:50], 1
        ):  # Increased to 50 rules for comprehensive coverage
            rule_content = rule.get("content", "")
            rule_type = rule.get("metadata", {}).get("rule_type", "unknown")
            # Show full content (up to 1000 chars) to give complete context
            prompt += f"{i}. [{rule_type.upper()}] {rule_content[:1000]}\n\n"
        prompt += "\nREMINDER: Only validate against the rules listed above. If a rule is not here, it does not apply.\n\n"
        prompt += "APPROVAL NUMBER VALIDATION:\n"
        prompt += "============================\n"
        approval_num = claim.get("approval_number", "")
        service_code = claim.get("service_code", "")
        diagnosis_codes = claim.get("diagnosis_codes", [])

        if approval_num and str(approval_num).strip().upper() not in [
            "N/A",
            "NONE",
            "NULL",
            "",
        ]:
            prompt += f"✓ Approval number is PRESENT: {approval_num}\n"
            prompt += "  - Check the rules above to see if approval is REQUIRED for this service code or diagnosis code.\n"
            prompt += "  - If approval is required per rules AND approval number is present, this is VALID.\n"
            prompt += "  - If approval is NOT required per rules, approval number is optional (can be present or absent).\n"
            prompt += "  - Do NOT flag as 'missing approval' if an approval number exists in the claim.\n"
            prompt += "  - Only flag as invalid if the approval format/type doesn't match requirements in the rules.\n\n"
        else:
            prompt += "⚠ Approval number is MISSING or empty.\n"
            prompt += "  - CRITICAL: Check the rules above to see if approval is REQUIRED for:\n"
            prompt += "    * Service code: Check if rules list this service in 'services_requiring_approval'\n"
            if diagnosis_codes:
                if isinstance(diagnosis_codes, list):
                    diag_list = ", ".join(map(str, diagnosis_codes))
                else:
                    diag_list = str(diagnosis_codes)
                prompt += f"    * Diagnosis code(s): {diag_list} - Check if rules list any diagnosis in 'diagnoses_requiring_approval'\n"
            prompt += "  - If EITHER service OR diagnosis requires approval per rules, but approval number is MISSING, this is a FAILURE.\n"
            prompt += "  - Only flag as missing approval if rules explicitly require it for this service/diagnosis.\n"
            prompt += "  - If rules do NOT require approval for this service/diagnosis, missing approval number is OK (PASS).\n\n"
    else:
        prompt += "\nRELEVANT ADJUDICATION RULES:\n"
        prompt += "=" * 50 + "\n"
        prompt += "NO RULES RETRIEVED: Since no relevant rules were found, you should report the claim as VALID for medical validation.\n"
        prompt += "Do NOT assume or infer rules that were not provided.\n\n"

    # Add technical passed rules if available
    technical_passed_rules = claim.get("technical_passed_rules", [])
    if technical_passed_rules and not has_errors:
        prompt += "\nTECHNICAL RULES VALIDATED:\n"
        prompt += "=" * 50 + "\n"
        prompt += "The following technical rules were checked and PASSED:\n\n"
        for i, rule in enumerate(technical_passed_rules, 1):
            prompt += f"{i}. {rule.get('rule', 'Unknown Rule')} ({rule.get('rule_reference', 'N/A')})\n"
            prompt += f"   ✓ {rule.get('detail', '')}\n\n"

    prompt += """
ANALYSIS REQUIREMENTS:
======================
Please provide a comprehensive analysis following this structure:

1. EXECUTIVE SUMMARY:
   - Brief overview of the claim's validation status based ONLY on the provided rules
   - Key findings and critical issues (if any) - MUST reference specific rule numbers
   - Overall assessment (VALID/INVALID/MANUAL_REVIEW_NEEDED) based ONLY on provided rules
   - MUST explicitly state if any medical rules from the provided rules are violated (with rule number)
   - If no violations found in provided rules, state: "No violations found in provided rules - claim is VALID"

2. DETAILED EXPLANATION:
   - You MUST explicitly check and report on EACH of these medical rule categories:
     a) SERVICE-DIAGNOSIS REQUIREMENTS CHECK:
        * Check if the service code in the claim requires a specific diagnosis code according to the rules.
        * If rules specify "Service X requires diagnosis Y", verify the claim's diagnosis matches.
        * If there's a mismatch, clearly state: "Service SRV2007 requires diagnosis E11.9 per rules, but claim has J45.909 - FAILURE"
        * If it matches, state: "Service SRV2007 requires diagnosis E11.9 per rules, claim has E11.9 - PASS"
     b) SERVICE-ENCOUNTER TYPE CHECK:
        * Check if the service is allowed for the encounter type (INPATIENT/OUTPATIENT).
        * Report: "Service SRV2007 is [allowed/not allowed] for OUTPATIENT encounter per rules - [PASS/FAIL]"
     c) FACILITY-SERVICE ELIGIBILITY CHECK:
        * Check if the facility type allows this service.
        * Report: "Service SRV2007 is [allowed/not allowed] for facility type per rules - [PASS/FAIL]"
     d) MUTUALLY EXCLUSIVE DIAGNOSES CHECK:
        * Check if any diagnoses are mutually exclusive.
        * Report: "No mutually exclusive diagnoses found - PASS" or "Diagnoses X and Y are mutually exclusive per rules - FAIL"
     e) APPROVAL REQUIREMENTS CHECK (MANDATORY):
        * FIRST: Check if SERVICE CODE requires approval per rules.
          - If rules list the service code in "services_requiring_approval", approval is REQUIRED.
          - Report: "Service [code] [requires/does not require] approval per rules"
        * SECOND: Check if DIAGNOSIS CODE requires approval per rules.
          - If rules list the diagnosis code in "diagnoses_requiring_approval", approval is REQUIRED.
          - Report: "Diagnosis [code] [requires/does not require] approval per rules"
        * THIRD: If approval is required (by service OR diagnosis):
          - Check if approval number is present in the claim.
          - Report: "Approval REQUIRED per rules, approval number [present/missing] - [PASS/FAIL]"
        * If approval is NOT required:
          - Report: "Approval not required per rules - PASS"
        * CRITICAL: If approval is REQUIRED but approval number is MISSING, this is ALWAYS a FAILURE.
   - If the claim is VALID (no violations):
     * List ALL medical rules from the provided rules that were checked and PASSED
     * For each passed rule, specify: "Rule #N: [rule content/description] - PASSED"
     * Include a summary like: "The claim complies with all medical rules checked: [list of rule numbers]"
   - If violations are found:
     * For each medical rule violation found, provide:
       * What the error is (be specific: "Service SRV2007 requires diagnosis E11.9 per rules, but claim has J45.909")
       * Which specific rule from the provided rules is being violated (include rule number or content)
       * Why it occurred (root cause analysis)
       * Impact on claim processing
   - IMPORTANT: Only reference rules that were provided above. Do NOT reference rules that were not listed.
   - MUST be explicit about any violations - do not be ambiguous
   - MUST cite the specific rule number or content when reporting a violation or passed rule
   - CRITICAL: If service-diagnosis requirements are specified in the rules and the claim doesn't match, this is ALWAYS a FAILURE

3. RECOMMENDATIONS:
   - Specific, actionable steps for the provider/claim administrator
   - Priority level for each recommendation (HIGH/MEDIUM/LOW)
   - Suggested corrective actions if errors are present
   - Preventive measures to avoid similar issues in the future

4. CONFIDENCE ASSESSMENT:
   - Your confidence level (0.0 to 1.0) in this evaluation
   - Factors affecting confidence (data completeness, rule clarity, etc.)
   - Any areas requiring additional review

5. ADDITIONAL NOTES:
   - Any anomalies, patterns, or observations worth noting
   - Potential edge cases or exceptions to consider

FORMAT YOUR RESPONSE AS:
=========================
EXECUTIVE_SUMMARY: [2-3 sentence summary]
VALIDATION_STATUS: 
  TECHNICAL_VALIDATION: [PASS/FAIL] 
  MEDICAL_VALIDATION: [PASS/FAIL]
  OVERALL_STATUS: [VALID/INVALID]
DETAILED_EXPLANATION: [comprehensive explanation, use bullet points for clarity]
TECHNICAL_RULES_STATUS:
  [For each technical rule checked, list one per line]
  - Rule Name: [PASS/FAIL] - [Brief reason]
MEDICAL_RULES_STATUS:
  [For each medical rule checked, list one per line]
  - Rule #N or Rule Name: [PASS/FAIL] - [Brief reason]
RECOMMENDATIONS: [numbered list of specific recommendations with priorities]
CONFIDENCE: [0.0-1.0 number]
NOTES: [any additional observations]

CRITICAL FORMATTING REQUIREMENTS:
- VALIDATION_STATUS must be on separate lines with TECHNICAL_VALIDATION, MEDICAL_VALIDATION, and OVERALL_STATUS
- Use exactly "PASS" or "FAIL" (all caps) for each validation type
- TECHNICAL_VALIDATION: 
  * Must be FAIL if ANY technical errors were listed above
  * Must be PASS ONLY if NO technical errors exist
  * Do NOT mark as PASS if technical errors are present
- MEDICAL_VALIDATION: 
  * Must be PASS if NO medical rule violations exist based on the provided rules
  * Must be FAIL if ANY medical rule from the provided rules is violated
  * Only validate against rules provided in "RELEVANT ADJUDICATION RULES" section
  * If no relevant medical rules are provided, default to PASS
- OVERALL_STATUS: Should be VALID only if both TECHNICAL_VALIDATION and MEDICAL_VALIDATION are PASS
- TECHNICAL_RULES_STATUS: List each technical rule that was checked with its status (PASS/FAIL)
- MEDICAL_RULES_STATUS: List each medical rule from the provided rules that was checked with its status (PASS/FAIL)
- Be explicit and clear about which rules passed and which failed
- Be thorough, professional, and ensure your recommendations are specific and actionable.
"""

    return prompt
