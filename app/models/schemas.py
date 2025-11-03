"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class ClaimBase(BaseModel):
    """Base claim schema."""

    claim_id: str
    encounter_type: Optional[str] = None
    service_date: Optional[datetime] = None
    national_id: Optional[str] = None
    member_id: Optional[str] = None
    facility_id: Optional[str] = None
    unique_id: Optional[str] = None
    diagnosis_codes: Optional[List[str]] = None
    service_code: Optional[str] = None
    paid_amount_aed: Optional[float] = None
    approval_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ClaimResponse(ClaimBase):
    """Claim response schema with validation results."""

    id: int
    status: str
    error_type: Optional[str] = None
    error_explanation: Optional[str] = None
    recommended_action: Optional[str] = None
    technical_errors: Optional[List[Dict[str, Any]]] = None
    medical_errors: Optional[List[Dict[str, Any]]] = None
    data_quality_errors: Optional[List[Dict[str, Any]]] = None
    llm_evaluated: bool = False
    llm_confidence_score: Optional[float] = None
    llm_explanation: Optional[str] = None
    tenant_id: str
    uploaded_by: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None


class ClaimsListResponse(BaseModel):
    """Response schema for claims list."""

    claims: List[ClaimResponse]
    total: int
    page: int
    page_size: int


class UploadResponse(BaseModel):
    """Response schema for file upload."""

    status: str
    batch_id: str
    total_claims: int
    validated: int
    not_validated: int
    processing_time_seconds: float
    metrics: Dict[str, Any]


class AnalyticsResponse(BaseModel):
    """Response schema for analytics data."""

    total_claims: int
    validated_claims: int
    not_validated_claims: int
    no_error_count: int
    technical_error_count: int
    medical_error_count: int
    both_errors_count: int
    total_paid_amount: float
    validated_amount: float
    rejected_amount: float
    waterfall_data: List[Dict[str, Any]]


class LoginRequest(BaseModel):
    """Login request schema."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str
    error_code: Optional[str] = None


class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    full_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """Schema for user creation."""

    password: str = Field(..., min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    tenant_id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SignUpRequest(UserCreate):
    """Sign up request schema."""

    pass


class SignUpResponse(BaseModel):
    """Sign up response schema."""

    user: UserResponse
    message: str

