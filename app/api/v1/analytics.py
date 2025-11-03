"""Analytics endpoints for validation metrics and charts."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, distinct, Integer, Numeric, case
from typing import Optional, List
from datetime import datetime, timedelta

from db.session import get_db
from models.database import ClaimMaster, ValidationMetrics
from dependencies import get_current_user, get_current_tenant
from models.database import User
from utils.logger import get_logger

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = get_logger(__name__)


@router.get("/metrics")
async def get_metrics(
    batch_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """
    Get aggregated validation metrics.
    
    Returns waterfall chart data and summary statistics.
    """
    try:
        # Build query filters
        query = db.query(ClaimMaster).filter(
            ClaimMaster.tenant_id == tenant_id
        )
        
        if batch_id:
            query = query.filter(ClaimMaster.batch_id == batch_id)
        
        if start_date:
            try:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                query = query.filter(ClaimMaster.created_at >= start)
            except ValueError:
                pass
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                query = query.filter(ClaimMaster.created_at <= end)
            except ValueError:
                pass
        
        all_claims = query.all()
        
        # Calculate metrics
        total_claims = len(all_claims)
        validated_claims = sum(1 for c in all_claims if c.status == "Validated")
        not_validated_claims = total_claims - validated_claims
        
        # Error type breakdown
        error_counts = {
            "No error": 0,
            "Technical error": 0,
            "Medical error": 0,
            "Both": 0,
        }
        
        for claim in all_claims:
            error_type = claim.error_type or "No error"
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        # Amount calculations
        total_amount = sum(float(c.paid_amount_aed or 0) for c in all_claims)
        validated_amount = sum(
            float(c.paid_amount_aed or 0) 
            for c in all_claims 
            if c.status == "Validated"
        )
        rejected_amount = total_amount - validated_amount
        
        # Waterfall chart data
        waterfall_data = [
            {"category": "Total Claims", "value": total_claims, "type": "start"},
            {"category": "No Error", "value": error_counts["No error"], "type": "positive"},
            {"category": "Technical Error", "value": -error_counts["Technical error"], "type": "negative"},
            {"category": "Medical Error", "value": -error_counts["Medical error"], "type": "negative"},
            {"category": "Both Errors", "value": -error_counts["Both"], "type": "negative"},
            {"category": "Validated", "value": validated_claims, "type": "end"},
        ]
        
        # Amount waterfall
        amount_waterfall = [
            {"category": "Total Amount", "value": total_amount, "type": "start"},
            {"category": "Validated", "value": validated_amount, "type": "positive"},
            {"category": "Rejected", "value": -rejected_amount, "type": "negative"},
        ]
        
        return {
            "summary": {
                "total_claims": total_claims,
                "validated_claims": validated_claims,
                "not_validated_claims": not_validated_claims,
                "validation_rate": (validated_claims / total_claims * 100) if total_claims > 0 else 0,
            },
            "error_breakdown": error_counts,
            "amounts": {
                "total_amount": total_amount,
                "validated_amount": validated_amount,
                "rejected_amount": rejected_amount,
            },
            "waterfall": waterfall_data,
            "amount_waterfall": amount_waterfall,
        }
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@router.get("/charts/error-breakdown")
async def get_error_breakdown_chart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Get error breakdown chart data."""
    claims = db.query(ClaimMaster).filter(
        ClaimMaster.tenant_id == tenant_id
    ).all()
    
    error_counts = {
        "No Error": 0,
        "Technical Error": 0,
        "Medical Error": 0,
        "Both Errors": 0,
    }
    
    for claim in claims:
        error_type = claim.error_type or "No Error"
        if error_type == "No error":
            error_counts["No Error"] += 1
        elif error_type == "Technical error":
            error_counts["Technical Error"] += 1
        elif error_type == "Medical error":
            error_counts["Medical Error"] += 1
        elif error_type == "Both":
            error_counts["Both Errors"] += 1
    
    chart_data = [
        {"category": k, "count": v}
        for k, v in error_counts.items()
    ]
    
    return chart_data


@router.get("/charts/amount-breakdown")
async def get_amount_breakdown_chart(
    batch_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Get paid amount breakdown by error category."""
    query = db.query(ClaimMaster).filter(
        ClaimMaster.tenant_id == tenant_id
    )
    if batch_id:
        query = query.filter(ClaimMaster.batch_id == batch_id)
    claims = query.all()
    
    amounts = {
        "No Error": 0,
        "Technical Error": 0,
        "Medical Error": 0,
        "Both Errors": 0,
    }
    
    for claim in claims:
        error_type = claim.error_type or "No Error"
        amount = float(claim.paid_amount_aed or 0)
        
        if error_type == "No error":
            amounts["No Error"] += amount
        elif error_type == "Technical error":
            amounts["Technical Error"] += amount
        elif error_type == "Medical error":
            amounts["Medical Error"] += amount
        elif error_type == "Both":
            amounts["Both Errors"] += amount
    
    chart_data = [
        {"category": k, "amount": v}
        for k, v in amounts.items()
    ]
    
    return chart_data


@router.get("/batches")
async def list_batches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Get list of all batches with summary statistics."""
    try:
        # Get distinct batch_ids with claim counts
        batches = (
            db.query(
                ClaimMaster.batch_id,
                func.count(ClaimMaster.id).label('claim_count'),
                func.min(ClaimMaster.created_at).label('created_at'),
                func.max(ClaimMaster.processed_at).label('processed_at'),
                func.sum(
                    case((ClaimMaster.status == "Validated", 1), else_=0)
                ).label('validated_count'),
                func.sum(func.coalesce(ClaimMaster.paid_amount_aed, 0)).label('total_amount'),
            )
            .filter(
                ClaimMaster.tenant_id == tenant_id,
                ClaimMaster.batch_id.isnot(None)
            )
            .group_by(ClaimMaster.batch_id)
            .order_by(func.min(ClaimMaster.created_at).desc())
            .all()
        )
        
        batch_list = []
        for batch in batches:
            batch_list.append({
                "batch_id": batch.batch_id,
                "claim_count": batch.claim_count or 0,
                "validated_count": int(batch.validated_count or 0),
                "total_amount": float(batch.total_amount or 0),
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
                "processed_at": batch.processed_at.isoformat() if batch.processed_at else None,
            })
        
        return {"batches": batch_list}
    except Exception as e:
        logger.error(f"Failed to list batches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve batches: {str(e)}")

