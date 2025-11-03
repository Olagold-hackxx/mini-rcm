"""Claims CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from db.session import get_db
from models.database import ClaimMaster
from dependencies import get_current_user, get_current_tenant
from models.database import User
from utils.logger import get_logger

router = APIRouter(prefix="/claims", tags=["claims"])
logger = get_logger(__name__)


@router.get("/")
async def list_claims(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    error_type: Optional[str] = None,
    batch_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """List claims with filtering and pagination."""
    try:
        query = db.query(ClaimMaster).filter(
            ClaimMaster.tenant_id == tenant_id
        )
        
        if status:
            query = query.filter(ClaimMaster.status == status)
        
        if error_type:
            query = query.filter(ClaimMaster.error_type == error_type)
        
        if batch_id:
            query = query.filter(ClaimMaster.batch_id == batch_id)
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (ClaimMaster.claim_id.ilike(search_filter)) |
                (ClaimMaster.member_id.ilike(search_filter)) |
                (ClaimMaster.national_id.ilike(search_filter))
            )
        
        total = query.count()
        claims = query.order_by(ClaimMaster.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "claims": [
                {
                    "claim_id": c.claim_id,
                    "encounter_type": c.encounter_type,
                    "service_date": c.service_date.isoformat() if c.service_date else None,
                    "national_id": c.national_id,
                    "member_id": c.member_id,
                    "facility_id": c.facility_id,
                    "unique_id": c.unique_id,
                    "diagnosis_codes": c.diagnosis_codes or [],
                    "service_code": c.service_code,
                    "paid_amount_aed": float(c.paid_amount_aed) if c.paid_amount_aed is not None else None,
                    "approval_number": c.approval_number,
                    "status": c.status,
                    "error_type": c.error_type or "No error",
                    "error_explanation": c.error_explanation,
                    "recommended_action": c.recommended_action,
                    "technical_errors": c.technical_errors or [],
                    "medical_errors": c.medical_errors or [],
                    "data_quality_errors": c.data_quality_errors or [],
                    "llm_evaluated": c.llm_evaluated or False,
                    "llm_confidence_score": float(c.llm_confidence_score) if c.llm_confidence_score is not None else None,
                    "llm_explanation": c.llm_explanation,
                    "uploaded_by": c.uploaded_by,
                    "batch_id": c.batch_id,
                    "processed_at": c.processed_at.isoformat() if c.processed_at else None,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in claims
            ],
        }
    except Exception as e:
        logger.error(f"Failed to list claims: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve claims: {str(e)}")


@router.get("/{claim_id}")
async def get_claim(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Get a single claim by ID."""
    claim = db.query(ClaimMaster).filter(
        ClaimMaster.claim_id == claim_id,
        ClaimMaster.tenant_id == tenant_id
    ).first()
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return {
        "claim_id": claim.claim_id,
        "encounter_type": claim.encounter_type,
        "service_date": claim.service_date.isoformat() if claim.service_date else None,
        "national_id": claim.national_id,
        "member_id": claim.member_id,
        "facility_id": claim.facility_id,
        "unique_id": claim.unique_id,
        "diagnosis_codes": claim.diagnosis_codes or [],
        "service_code": claim.service_code,
        "paid_amount_aed": float(claim.paid_amount_aed) if claim.paid_amount_aed is not None else None,
        "approval_number": claim.approval_number,
        "status": claim.status,
        "error_type": claim.error_type or "No error",
        "error_explanation": claim.error_explanation,
        "recommended_action": claim.recommended_action,
        "technical_errors": claim.technical_errors or [],
        "medical_errors": claim.medical_errors or [],
        "data_quality_errors": claim.data_quality_errors or [],
        "llm_evaluated": claim.llm_evaluated or False,
        "llm_confidence_score": float(claim.llm_confidence_score) if claim.llm_confidence_score is not None else None,
        "llm_explanation": claim.llm_explanation,
        "llm_retrieved_rules": claim.llm_retrieved_rules or [],
        "uploaded_by": claim.uploaded_by,
        "batch_id": claim.batch_id,
        "uploaded_at": claim.uploaded_at.isoformat() if claim.uploaded_at else None,
        "processed_at": claim.processed_at.isoformat() if claim.processed_at else None,
        "created_at": claim.created_at.isoformat() if claim.created_at else None,
    }

