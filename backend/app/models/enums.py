"""Enum definitions for the application."""
from enum import Enum


class ClaimStatus(str, Enum):
    """Claim validation status."""

    PROCESSING = "Processing"
    VALIDATED = "Validated"
    NOT_VALIDATED = "Not validated"


class ErrorType(str, Enum):
    """Error type classification."""

    NO_ERROR = "No error"
    TECHNICAL_ERROR = "Technical error"
    MEDICAL_ERROR = "Medical error"
    BOTH = "Both"
    DATA_QUALITY_ERROR = "Data quality error"


class EncounterType(str, Enum):
    """Encounter type values."""

    INPATIENT = "INPATIENT"
    OUTPATIENT = "OUTPATIENT"


class RuleType(str, Enum):
    """Rule document type."""

    TECHNICAL = "technical"
    MEDICAL = "medical"

