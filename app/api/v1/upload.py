"""File upload endpoints."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pathlib import Path
import aiofiles
import uuid
import re

from db.session import get_db
from models.database import User
from dependencies import get_current_user, get_current_tenant
from models.schemas import UploadResponse
from pipeline.orchestrator import PipelineOrchestrator
from config import get_settings
from utils.logger import get_logger

router = APIRouter(prefix="/upload", tags=["upload"])
settings = get_settings()
logger = get_logger(__name__)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/claims", response_model=UploadResponse)
async def upload_claims_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Upload and process claims file."""
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )
    
    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    
    try:
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"File uploaded: {file_path}")
        
        # Process file through pipeline
        orchestrator = PipelineOrchestrator(db, tenant_id)
        result = await orchestrator.process_claims_file(
            str(file_path), current_user.username
        )
        
        return result
    except IntegrityError as e:
        # Handle database integrity errors (like duplicate keys) with cleaner messages
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        
        # Extract claim_id from error message if it's a unique constraint violation
        if "ix_claims_master_claim_id" in error_msg or "duplicate key" in error_msg.lower():
            claim_id_match = re.search(r'claim_id\)=\(([^)]+)\)', error_msg)
            if claim_id_match:
                claim_id = claim_id_match.group(1)
                logger.error(f"Duplicate claim_id detected: {claim_id}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Claim ID '{claim_id}' already exists in the database. Please ensure claim IDs are unique or re-upload the file."
                )
        
        logger.error(f"Database integrity error: {error_msg}")
        raise HTTPException(
            status_code=400,
            detail="A database constraint was violated. This usually means duplicate data. Please check your file and try again."
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Handle other errors with cleaner messages
        error_msg = str(e)
        logger.error(f"File processing failed: {e}", exc_info=True)
        
        # Truncate very long error messages
        if len(error_msg) > 500:
            error_msg = error_msg[:500] + "... (error message truncated)"
        
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {error_msg}"
        )
    finally:
        # Clean up uploaded file
        if file_path.exists():
            file_path.unlink()

