"""File upload endpoints."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pathlib import Path
import aiofiles
import uuid

from app.db.session import get_db
from app.dependencies import get_current_user, get_current_tenant
from app.models.schemas import UploadResponse
from app.pipeline.orchestrator import PipelineOrchestrator
from app.config import get_settings
from app.utils.logger import get_logger

router = APIRouter(prefix="/upload", tags=["upload"])
settings = get_settings()
logger = get_logger(__name__)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/claims", response_model=UploadResponse)
async def upload_claims_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
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
            str(file_path), current_user["username"]
        )
        
        return result
    except Exception as e:
        logger.error(f"File processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        # Clean up uploaded file
        if file_path.exists():
            file_path.unlink()

