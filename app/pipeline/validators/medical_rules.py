"""Medical rules engine for adjudication."""
import json
from typing import List, Dict
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class MedicalRulesEngine:
    """Implements medical adjudication rules."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict:
        """Load medical rules configuration."""
        rules_path = Path(f"app/rules/{self.tenant_id}/medical_rules.json")
        if not rules_path.exists():
            rules_path = Path("app/rules/default/medical_rules.json")
        
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
        
        errors.extend(self._check_service_encounter_type(claim))
        errors.extend(self._check_facility_service_eligibility(claim))
        errors.extend(self._check_service_diagnosis_requirements(claim))
        errors.extend(self._check_mutually_exclusive_diagnoses(claim))
        
        return errors

    def _check_service_encounter_type(self, claim: Dict) -> List[Dict]:
        """Check if service is allowed for encounter type (A. Services limited by Encounter Type)."""
        errors = []
        encounter_type = claim.get("encounter_type")
        service_code = claim.get("service_code")
        
        if not encounter_type or not service_code:
            return errors
        
        encounter_type = str(encounter_type).upper().strip()
        service_code = str(service_code).strip()
        
        inpatient_services = self.rules.get("inpatient_services", [])
        outpatient_services = self.rules.get("outpatient_services", [])
        
        if encounter_type == "INPATIENT":
            if service_code not in inpatient_services:
                errors.append({
                    "type": "Medical error",
                    "rule": "Service-Encounter Type Restriction",
                    "rule_reference": "Medical Rules Section A",
                    "detail": (
                        f"Service code {service_code} is not allowed for "
                        f"INPATIENT encounters. Allowed services: {inpatient_services}"
                    ),
                    "severity": "error",
                })
        elif encounter_type == "OUTPATIENT":
            if service_code not in outpatient_services:
                errors.append({
                    "type": "Medical error",
                    "rule": "Service-Encounter Type Restriction",
                    "rule_reference": "Medical Rules Section A",
                    "detail": (
                        f"Service code {service_code} is not allowed for "
                        f"OUTPATIENT encounters. Allowed services: {outpatient_services}"
                    ),
                    "severity": "error",
                })
        
        return errors

    def _check_facility_service_eligibility(self, claim: Dict) -> List[Dict]:
        """Check if facility is eligible for the service (B. Services limited by Facility Type)."""
        errors = []
        facility_id = claim.get("facility_id")
        service_code = claim.get("service_code")
        
        if not facility_id or not service_code:
            return errors
        
        facility_id = str(facility_id).strip()
        service_code = str(service_code).strip()
        
        facility_registry = self.rules.get("facility_registry", {})
        facility_types = self.rules.get("facility_types", {})
        
        # Get facility type from registry
        facility_type = facility_registry.get(facility_id)
        if not facility_type:
            # Facility not in registry - this might be an error, but allow it for now
            return errors
        
        # Get allowed services for this facility type
        allowed_services = facility_types.get(facility_type, [])
        
        if service_code not in allowed_services:
            errors.append({
                "type": "Medical error",
                "rule": "Facility-Service Eligibility",
                "rule_reference": "Medical Rules Section B",
                "detail": (
                    f"Facility {facility_id} (type: {facility_type}) is not eligible "
                    f"for service code {service_code}. Allowed services: {allowed_services}"
                ),
                "severity": "error",
            })
        
        return errors

    def _check_service_diagnosis_requirements(self, claim: Dict) -> List[Dict]:
        """Check if service requires specific diagnosis (C. Services requiring specific Diagnoses)."""
        errors = []
        service_code = claim.get("service_code")
        diagnosis_codes = claim.get("diagnosis_codes", [])
        
        if not service_code or not diagnosis_codes:
            return errors
        
        if not isinstance(diagnosis_codes, list):
            diagnosis_codes = [diagnosis_codes]
        
        service_code = str(service_code).strip()
        service_diagnosis_requirements = self.rules.get(
            "service_diagnosis_requirements", {}
        )
        
        if service_code in service_diagnosis_requirements:
            required_diagnoses = service_diagnosis_requirements[service_code]
            if not any(dx in required_diagnoses for dx in diagnosis_codes):
                errors.append({
                    "type": "Medical error",
                    "rule": "Service-Diagnosis Requirement",
                    "rule_reference": "Medical Rules Section C",
                    "detail": (
                        f"Service code {service_code} requires one of the following "
                        f"diagnosis codes: {required_diagnoses}, but found: {diagnosis_codes}"
                    ),
                    "severity": "error",
                })
        
        return errors

    def _check_mutually_exclusive_diagnoses(self, claim: Dict) -> List[Dict]:
        """Check for mutually exclusive diagnoses (D. Mutually Exclusive Diagnoses)."""
        errors = []
        diagnosis_codes = claim.get("diagnosis_codes", [])
        
        if not diagnosis_codes:
            return errors
        
        if not isinstance(diagnosis_codes, list):
            diagnosis_codes = [diagnosis_codes]
        
        mutually_exclusive = self.rules.get("mutually_exclusive_diagnoses", [])
        
        for exclusion_rule in mutually_exclusive:
            exclusion_diagnoses = exclusion_rule.get("diagnoses", [])
            reason = exclusion_rule.get("reason", "Cannot coexist")
            
            # Check if both diagnoses are present
            if all(dx in diagnosis_codes for dx in exclusion_diagnoses):
                errors.append({
                    "type": "Medical error",
                    "rule": "Mutually Exclusive Diagnoses",
                    "rule_reference": "Medical Rules Section D",
                    "detail": (
                        f"The following diagnosis codes cannot coexist: {exclusion_diagnoses}. "
                        f"Reason: {reason}"
                    ),
                    "severity": "error",
                })
        
        return errors

