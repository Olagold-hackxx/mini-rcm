"""Technical rules engine for adjudication."""
import json
import re
from typing import List, Dict
from pathlib import Path
from utils.logger import get_logger
from services.rule_config_service import RuleConfigService

logger = get_logger(__name__)


class TechnicalRulesEngine:
    """Implements technical adjudication rules with dynamic configuration."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._rules = None
    
    @property
    def rules(self) -> Dict:
        """Lazy-load rules using RuleConfigService (supports dynamic updates)."""
        if self._rules is None:
            self._rules = RuleConfigService.get_technical_rules(self.tenant_id)
        return self._rules
    
    def reload_rules(self):
        """Reload rules from configuration (useful after updates)."""
        RuleConfigService.invalidate_cache(self.tenant_id, "technical")
        self._rules = None

    def validate(self, claim: Dict) -> tuple[List[Dict], List[Dict]]:
        """
        Validate claim against technical rules.
        
        Returns:
            Tuple of (errors, passed_rules) - lists of rule validation results
        """
        errors = []
        passed_rules = []
        
        # Check service approval
        service_errors = self._check_service_approval(claim)
        errors.extend(service_errors)
        if not service_errors:
            service_code = claim.get("service_code")
            approval_number = claim.get("approval_number")
            services_requiring_approval = self.rules.get("services_requiring_approval", [])
            if service_code:
                if str(service_code) in services_requiring_approval:
                    if approval_number and str(approval_number).strip():
                        passed_rules.append({
                            "rule": "Service Approval Requirement",
                            "rule_reference": "Technical Rules Section 1",
                            "detail": f"Service code {service_code} requires approval and approval number {approval_number} is provided."
                        })
                else:
                    passed_rules.append({
                        "rule": "Service Approval Requirement",
                        "rule_reference": "Technical Rules Section 1",
                        "detail": f"Service code {service_code} does not require prior approval."
                    })
        
        # Check diagnosis approval
        diagnosis_errors = self._check_diagnosis_approval(claim)
        errors.extend(diagnosis_errors)
        if not diagnosis_errors:
            diagnosis_codes = claim.get("diagnosis_codes", [])
            approval_number = claim.get("approval_number")
            diagnoses_requiring_approval = self.rules.get("diagnoses_requiring_approval", [])
            if diagnosis_codes:
                diagnosis_list = diagnosis_codes if isinstance(diagnosis_codes, list) else [diagnosis_codes]
                requires_approval = any(str(d).strip() in diagnoses_requiring_approval for d in diagnosis_list)
                if requires_approval:
                    if approval_number and str(approval_number).strip():
                        passed_rules.append({
                            "rule": "Diagnosis Approval Requirement",
                            "rule_reference": "Technical Rules Section 2",
                            "detail": f"Diagnosis code(s) {', '.join(map(str, diagnosis_list))} require approval and approval number {approval_number} is provided."
                        })
                else:
                    passed_rules.append({
                        "rule": "Diagnosis Approval Requirement",
                        "rule_reference": "Technical Rules Section 2",
                        "detail": f"Diagnosis code(s) {', '.join(map(str, diagnosis_list))} do not require prior approval."
                    })
        
        # Check paid amount threshold
        amount_errors = self._check_paid_amount_threshold(claim)
        errors.extend(amount_errors)
        if not amount_errors:
            paid_amount = claim.get("paid_amount_aed", 0)
            threshold = self.rules.get("paid_amount_threshold", 5000.0)
            if paid_amount and float(paid_amount) <= threshold:
                passed_rules.append({
                    "rule": "Paid Amount Threshold",
                    "rule_reference": "Technical Rules Section 3",
                    "detail": f"Paid amount {paid_amount} AED is within threshold of {threshold} AED."
                })
        
        # Check unique ID format
        unique_id_errors = self._check_unique_id_format(claim)
        errors.extend(unique_id_errors)
        if not unique_id_errors:
            unique_id = claim.get("unique_id")
            if unique_id:
                passed_rules.append({
                    "rule": "Unique ID Format",
                    "rule_reference": "Technical Rules Section 4",
                    "detail": f"Unique ID {unique_id} format is valid."
                })
        
        return errors, passed_rules

    def _check_service_approval(self, claim: Dict) -> List[Dict]:
        """Check if service requires prior approval."""
        errors = []
        service_code = claim.get("service_code")
        approval_number = claim.get("approval_number")
        
        if not service_code:
            return errors
        
        services_requiring_approval = self.rules.get(
            "services_requiring_approval", []
        )
        
        if str(service_code) in services_requiring_approval:
            if not approval_number or str(approval_number).strip() == "":
                errors.append({
                    "type": "Technical error",
                    "rule": "Service Requires Prior Approval",
                    "rule_reference": "Technical Rules Section 1",
                    "detail": (
                        f"Service code {service_code} requires prior approval "
                        "but no approval number provided"
                    ),
                    "severity": "critical",
                })
        
        return errors

    def _check_diagnosis_approval(self, claim: Dict) -> List[Dict]:
        """Check if diagnosis requires prior approval."""
        errors = []
        diagnosis_codes = claim.get("diagnosis_codes", [])
        approval_number = claim.get("approval_number")
        
        if not isinstance(diagnosis_codes, list):
            diagnosis_codes = [diagnosis_codes] if diagnosis_codes else []
        
        diagnoses_requiring_approval = self.rules.get(
            "diagnoses_requiring_approval", []
        )
        
        for dx_code in diagnosis_codes:
            if dx_code in diagnoses_requiring_approval:
                if not approval_number or str(approval_number).strip() == "":
                    errors.append({
                        "type": "Technical error",
                        "rule": "Diagnosis Requires Prior Approval",
                        "rule_reference": "Technical Rules Section 2",
                        "detail": (
                            f"Diagnosis code {dx_code} requires prior approval "
                            "but no approval number provided"
                        ),
                        "severity": "critical",
                    })
                    break  # Only report once
        
        return errors

    def _check_paid_amount_threshold(self, claim: Dict) -> List[Dict]:
        """Check if paid amount exceeds threshold."""
        errors = []
        paid_amount = claim.get("paid_amount_aed")
        
        if not paid_amount:
            return errors
        
        try:
            amount = float(paid_amount)
            threshold = self.rules.get("paid_amount_threshold", 5000.0)
            
            if amount > threshold:
                errors.append({
                    "type": "Technical error",
                    "rule": "Paid Amount Threshold",
                    "rule_reference": "Technical Rules Section 3",
                    "detail": (
                        f"Paid amount {amount} exceeds threshold {threshold}. "
                        "Requires additional approval."
                    ),
                    "severity": "warning",
                })
        except (ValueError, TypeError):
            pass  # Already handled in data quality stage
        
        return errors

    def _check_unique_id_format(self, claim: Dict) -> List[Dict]:
        """Check unique_id format and structure."""
        errors = []
        unique_id = claim.get("unique_id")
        national_id = claim.get("national_id")
        member_id = claim.get("member_id")
        facility_id = claim.get("facility_id")
        
        if not unique_id:
            return errors
        
        unique_id = str(unique_id).strip()
        pattern = self.rules.get("unique_id_pattern", r"^[A-Z0-9-]{10,}$")
        
        # Check format pattern
        if not re.match(pattern, unique_id):
            errors.append({
                "type": "Technical error",
                "rule": "Unique ID Format",
                "rule_reference": "Technical Rules Section 4",
                "detail": (
                    f"Unique ID format is invalid: {unique_id}. "
                    f"Expected pattern: {pattern}"
                ),
                "severity": "error",
            })
            return errors
        
        # Verify segment sources if configured and data is available
        unique_id_validation = self.rules.get("unique_id_validation", {})
        if unique_id_validation.get("verify_segments") and national_id and member_id and facility_id:
            # Expected format: first4(National ID) – middle4(Member ID) – last4(Facility ID)
            national_str = str(national_id).strip().upper()
            member_str = str(member_id).strip().upper()
            facility_str = str(facility_id).strip().upper()
            
            expected_first4 = national_str[:4] if len(national_str) >= 4 else national_str
            expected_middle4 = member_str[:4] if len(member_str) >= 4 else member_str
            expected_last4 = facility_str[:4] if len(facility_str) >= 4 else facility_str
            
            parts = unique_id.split("-")
            if len(parts) == 3:
                actual_first = parts[0]
                actual_middle = parts[1]
                actual_last = parts[2]
                
                if actual_first != expected_first4:
                    errors.append({
                        "type": "Technical error",
                        "rule": "Unique ID Segment Validation",
                        "rule_reference": "Technical Rules Section 4",
                        "detail": (
                            f"Unique ID first segment '{actual_first}' does not match "
                            f"first 4 characters of National ID '{expected_first4}'"
                        ),
                        "severity": "error",
                    })
                
                if actual_middle != expected_middle4:
                    errors.append({
                        "type": "Technical error",
                        "rule": "Unique ID Segment Validation",
                        "rule_reference": "Technical Rules Section 4",
                        "detail": (
                            f"Unique ID middle segment '{actual_middle}' does not match "
                            f"first 4 characters of Member ID '{expected_middle4}'"
                        ),
                        "severity": "error",
                    })
                
                if actual_last != expected_last4:
                    errors.append({
                        "type": "Technical error",
                        "rule": "Unique ID Segment Validation",
                        "rule_reference": "Technical Rules Section 4",
                        "detail": (
                            f"Unique ID last segment '{actual_last}' does not match "
                            f"first 4 characters of Facility ID '{expected_last4}'"
                        ),
                        "severity": "error",
                    })
            
            # Check casing - all should be uppercase
            if unique_id != unique_id.upper():
                errors.append({
                    "type": "Technical error",
                    "rule": "Unique ID Casing",
                    "rule_reference": "Technical Rules Section 4",
                    "detail": (
                        "All IDs must be UPPERCASE alphanumeric. "
                        f"Found: {unique_id}"
                    ),
                    "severity": "error",
                })
        
        return errors

