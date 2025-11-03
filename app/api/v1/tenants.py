"""API endpoints for tenant management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import re
from pathlib import Path
import json

from db.session import get_db
from dependencies import get_current_user, get_current_tenant
from models.database import User
from services.rule_config_service import RuleConfigService
from utils.logger import get_logger
from config import get_settings

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


class CreateTenantRequest(BaseModel):
    """Request model for creating a new tenant."""
    tenant_id: str = Field(..., min_length=3, max_length=50, description="Unique tenant identifier")
    copy_from_default: bool = Field(default=True, description="Copy rules from default tenant")


class TenantResponse(BaseModel):
    """Response model for tenant information."""
    tenant_id: str
    exists: bool
    has_custom_rules: bool
    technical_rules_path: Optional[str] = None
    medical_rules_path: Optional[str] = None


@router.post("/tenants/create")
async def create_tenant(
    request: CreateTenantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new tenant and optionally copy rules from default.
    Users can create their own tenant to customize rules without affecting default.
    """
    # Validate tenant_id format (alphanumeric, underscore, hyphen)
    if not re.match(r"^[a-zA-Z0-9_-]+$", request.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id can only contain letters, numbers, underscores, and hyphens"
        )
    
    # Prevent creating "default" tenant
    if request.tenant_id.lower() == "default":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a tenant with ID 'default'. This is reserved."
        )
    
    # Check if tenant directory already exists
    tenant_dir = Path(f"app/rules/{request.tenant_id}")
    if tenant_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant '{request.tenant_id}' already exists"
        )
    
    try:
        # Create tenant directory
        tenant_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy rules from default if requested
        TECHNICAL_RULES_FILE = "technical_rules.json"
        MEDICAL_RULES_FILE = "medical_rules.json"
        
        if request.copy_from_default:
            default_technical = Path("app/rules/default") / TECHNICAL_RULES_FILE
            default_medical = Path("app/rules/default") / MEDICAL_RULES_FILE
            
            if default_technical.exists():
                tenant_technical = tenant_dir / TECHNICAL_RULES_FILE
                # Using synchronous file operations for small JSON files is acceptable
                with open(default_technical, 'r') as src, open(tenant_technical, 'w') as dst:
                    json.dump(json.load(src), dst, indent=2)
                logger.info(f"Copied technical rules to {tenant_technical}")
            
            if default_medical.exists():
                tenant_medical = tenant_dir / MEDICAL_RULES_FILE
                # Using synchronous file operations for small JSON files is acceptable
                with open(default_medical, 'r') as src, open(tenant_medical, 'w') as dst:
                    json.dump(json.load(src), dst, indent=2)
                logger.info(f"Copied medical rules to {tenant_medical}")
        else:
            # Create empty rule files with defaults
            technical_rules = RuleConfigService._get_default_rules("technical")
            medical_rules = RuleConfigService._get_default_rules("medical")
            
            # Using synchronous file operations for small JSON files is acceptable
            with open(tenant_dir / TECHNICAL_RULES_FILE, 'w') as f:
                json.dump(technical_rules, f, indent=2)
            
            with open(tenant_dir / MEDICAL_RULES_FILE, 'w') as f:
                json.dump(medical_rules, f, indent=2)
        
        # Update user's tenant_id
        current_user.tenant_id = request.tenant_id
        db.commit()
        db.refresh(current_user)
        
        # Invalidate cache for new tenant
        RuleConfigService.invalidate_cache(request.tenant_id)
        
        logger.info(f"Created tenant '{request.tenant_id}' for user {current_user.username}")
        
        return {
            "status": "success",
            "message": f"Tenant '{request.tenant_id}' created successfully",
            "tenant_id": request.tenant_id,
            "user_updated": True,
        }
    
    except Exception as e:
        logger.error(f"Failed to create tenant '{request.tenant_id}': {e}")
        # Cleanup on failure
        if tenant_dir.exists():
            import shutil
            shutil.rmtree(tenant_dir)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tenant: {str(e)}"
        )


@router.post("/tenants/switch")
async def switch_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Switch current user to a different tenant.
    User must have access to the tenant (for now, any existing tenant).
    """
    # Validate tenant_id format
    if not re.match(r"^[a-zA-Z0-9_-]+$", tenant_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant_id format"
        )
    
    # Check if tenant exists (has rules directory)
    tenant_dir = Path(f"app/rules/{tenant_id}")
    if not tenant_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' does not exist. Create it first."
        )
    
    # Update user's tenant_id
    current_user.tenant_id = tenant_id
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"User {current_user.username} switched to tenant '{tenant_id}'")
    
    return {
        "status": "success",
        "message": f"Switched to tenant '{tenant_id}'",
        "tenant_id": tenant_id,
    }


@router.get("/tenants/current")
async def get_current_tenant_info(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Get information about the current tenant."""
    TECHNICAL_RULES_FILE = "technical_rules.json"
    MEDICAL_RULES_FILE = "medical_rules.json"
    
    tenant_dir = Path(f"app/rules/{tenant_id}")
    technical_path = tenant_dir / TECHNICAL_RULES_FILE
    medical_path = tenant_dir / MEDICAL_RULES_FILE
    
    has_custom_rules = technical_path.exists() or medical_path.exists()
    
    return TenantResponse(
        tenant_id=tenant_id,
        exists=tenant_dir.exists(),
        has_custom_rules=has_custom_rules,
        technical_rules_path=str(technical_path) if technical_path.exists() else None,
        medical_rules_path=str(medical_path) if medical_path.exists() else None,
    )


@router.get("/tenants/list")
async def list_tenants(
    current_user: User = Depends(get_current_user),
):
    """List all available tenants (based on existing rule directories)."""
    rules_dir = Path("app/rules")
    
    if not rules_dir.exists():
        return {"tenants": []}
    
    TECHNICAL_RULES_FILE = "technical_rules.json"
    MEDICAL_RULES_FILE = "medical_rules.json"
    
    tenants = []
    for item in rules_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            tenant_id = item.name
            technical_exists = (item / TECHNICAL_RULES_FILE).exists()
            medical_exists = (item / MEDICAL_RULES_FILE).exists()
            
            tenants.append({
                "tenant_id": tenant_id,
                "has_rules": technical_exists or medical_exists,
                "is_default": tenant_id == "default",
                "is_current": tenant_id == current_user.tenant_id,
            })
    
    return {"tenants": sorted(tenants, key=lambda x: (x["is_current"], x["tenant_id"]))}

