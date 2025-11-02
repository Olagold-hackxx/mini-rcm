"""Medical rules engine for adjudication."""
import json
from typing import List, Dict
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MedicalRulesEngine:
    """Implements medical adjudication rules."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict:
        """Load medical rules configuration."""
        rules_path = Path(f"backend/rules/{self.tenant_id}/medical_rules.json")
        if not rules_path.exists():
            rules_path = Path("backend/rules/default/medical_rules.json")
        
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
        """Get default medical rules."""
        return {
            "inpatient_facilities": ["FAC-101", "FAC-102"],
            "outpatient_facilities": ["FAC-103", "FAC-104"],
            "service_diagnosis_mapping": {
                "99213": ["J18.9", "R50.9"],
                "99223": ["I10", "E11.9"],
            },
            "diagnosis_encounter_restrictions": {
                "I10": ["INPATIENT"],
                "E11.9": ["INPATIENT", "OUTPATIENT"],
            },
        }

    def validate(self, claim: Dict) -> List[Dict]:
        """Validate claim against medical rules."""
        errors = []
        
        errors.extend(self._check_facility_eligibility(claim))
        errors.extend(self._check_service_diagnosis_alignment(claim))
        errors.extend(self._check_diagnosis_encounter_restrictions(claim))
        
        return errors

    def _check_facility_eligibility(self, claim: Dict) -> List[Dict]:
        """Check if facility is eligible for encounter type."""
        errors = []
        encounter_type = claim.get("encounter_type")
        facility_id = claim.get("facility_id")
        
        if not encounter_type or not facility_id:
            return errors
        
        encounter_type = str(encounter_type).upper().strip()
        facility_id = str(facility_id).strip()
        
        inpatient_facilities = self.rules.get("inpatient_facilities", [])
        outpatient_facilities = self.rules.get("outpatient_facilities", [])
        
        if encounter_type == "INPATIENT":
            if facility_id not in inpatient_facilities:
                errors.append({
                    "type": "Medical error",
                    "rule": "Facility Eligibility - Inpatient",
                    "rule_reference": "Medical Rules Section 1",
                    "detail": (
                        f"Facility {facility_id} is not eligible for "
                        f"INPATIENT encounters"
                    ),
                    "severity": "error",
                })
        elif encounter_type == "OUTPATIENT":
            if facility_id not in outpatient_facilities:
                errors.append({
                    "type": "Medical error",
                    "rule": "Facility Eligibility - Outpatient",
                    "rule_reference": "Medical Rules Section 1",
                    "detail": (
                        f"Facility {facility_id} is not eligible for "
                        f"OUTPATIENT encounters"
                    ),
                    "severity": "error",
                })
        
        return errors

    def _check_service_diagnosis_alignment(self, claim: Dict) -> List[Dict]:
        """Check if service code aligns with diagnosis codes."""
        errors = []
        service_code = claim.get("service_code")
        diagnosis_codes = claim.get("diagnosis_codes", [])
        
        if not service_code or not diagnosis_codes:
            return errors
        
        if not isinstance(diagnosis_codes, list):
            diagnosis_codes = [diagnosis_codes]
        
        service_diagnosis_mapping = self.rules.get(
            "service_diagnosis_mapping", {}
        )
        
        if service_code in service_diagnosis_mapping:
            allowed_diagnoses = service_diagnosis_mapping[service_code]
            if not any(dx in allowed_diagnoses for dx in diagnosis_codes):
                errors.append({
                    "type": "Medical error",
                    "rule": "Service-Diagnosis Alignment",
                    "rule_reference": "Medical Rules Section 2",
                    "detail": (
                        f"Service code {service_code} does not align with "
                        f"diagnosis codes {diagnosis_codes}"
                    ),
                    "severity": "error",
                })
        
        return errors

    def _check_diagnosis_encounter_restrictions(self, claim: Dict) -> List[Dict]:
        """Check if diagnosis is allowed for encounter type."""
        errors = []
        encounter_type = claim.get("encounter_type")
        diagnosis_codes = claim.get("diagnosis_codes", [])
        
        if not encounter_type or not diagnosis_codes:
            return errors
        
        if not isinstance(diagnosis_codes, list):
            diagnosis_codes = [diagnosis_codes]
        
        encounter_type = str(encounter_type).upper().strip()
        restrictions = self.rules.get(
            "diagnosis_encounter_restrictions", {}
        )
        
        for dx_code in diagnosis_codes:
            if dx_code in restrictions:
                allowed_encounters = restrictions[dx_code]
                if encounter_type not in allowed_encounters:
                    errors.append({
                        "type": "Medical error",
                        "rule": "Diagnosis-Encounter Restriction",
                        "rule_reference": "Medical Rules Section 3",
                        "detail": (
                            f"Diagnosis code {dx_code} is not allowed for "
                            f"{encounter_type} encounters"
                        ),
                        "severity": "error",
                    })
        
        return errors

