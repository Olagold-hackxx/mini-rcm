"""Technical rules engine for adjudication."""
import json
import re
from typing import List, Dict
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TechnicalRulesEngine:
    """Implements technical adjudication rules."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict:
        """Load technical rules configuration."""
        rules_path = Path(f"backend/rules/{self.tenant_id}/technical_rules.json")
        if not rules_path.exists():
            rules_path = Path("backend/rules/default/technical_rules.json")
        
        if not rules_path.exists():
            logger.warning(f"Rules file not found: {rules_path}, using defaults")
            return self._get_default_rules()
        
        try:
            with open(rules_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load rules: {e}, using defaults")
            return self._get_default_rules()

    def _get_default_rules(self) -> Dict:
        """Get default technical rules."""
        return {
            "services_requiring_approval": ["99223", "99233", "99213"],
            "diagnoses_requiring_approval": ["I10", "E11.9"],
            "paid_amount_threshold": 5000.0,
            "unique_id_pattern": r"^[A-Z0-9-]{10,}$",
        }

    def validate(self, claim: Dict) -> List[Dict]:
        """Validate claim against technical rules."""
        errors = []
        
        errors.extend(self._check_service_approval(claim))
        errors.extend(self._check_diagnosis_approval(claim))
        errors.extend(self._check_paid_amount_threshold(claim))
        errors.extend(self._check_unique_id_format(claim))
        
        return errors

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
        """Check unique_id format."""
        errors = []
        unique_id = claim.get("unique_id")
        
        if not unique_id:
            return errors
        
        pattern = self.rules.get("unique_id_pattern", r"^[A-Z0-9-]{10,}$")
        
        if not re.match(pattern, str(unique_id)):
            errors.append({
                "type": "Technical error",
                "rule": "Unique ID Format",
                "rule_reference": "Technical Rules Section 4",
                "detail": f"Unique ID format is invalid: {unique_id}",
                "severity": "error",
            })
        
        return errors

