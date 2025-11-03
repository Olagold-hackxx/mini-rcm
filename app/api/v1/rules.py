"""API endpoints for managing tenant-specific rule configurations."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional
from sqlalchemy.orm import Session
import json

from db.session import get_db
from dependencies import get_current_user, get_current_tenant
from models.database import User
from services.rule_config_service import RuleConfigService
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Constants
VALID_RULE_TYPES = ["technical", "medical"]
INVALID_RULE_TYPE_MSG = "rule_type must be 'technical' or 'medical'"


@router.get("/rules")
async def get_rules(
    rule_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """
    Get current rule configuration for the tenant.
    
    Args:
        rule_type: "technical" or "medical" (optional, returns both if not specified)
    """
    try:
        if rule_type:
            if rule_type not in VALID_RULE_TYPES:
                raise HTTPException(status_code=400, detail=INVALID_RULE_TYPE_MSG)
            
            rules = RuleConfigService.get_rules(tenant_id, rule_type)
            return {rule_type: rules}
        else:
            # Return both rule types
            technical_rules = RuleConfigService.get_technical_rules(tenant_id)
            medical_rules = RuleConfigService.get_medical_rules(tenant_id)
            return {
                "technical": technical_rules,
                "medical": medical_rules,
            }
    except Exception as e:
        logger.error(f"Failed to get rules for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve rules: {str(e)}")


@router.put("/rules/{rule_type}")
async def update_rules(
    rule_type: str,
    rules: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """
    Update rule configuration for the tenant.
    Rules are saved to file and cache is invalidated.
    
    Args:
        rule_type: "technical" or "medical"
        rules: JSON object with rule configuration
    """
    if rule_type not in VALID_RULE_TYPES:
        raise HTTPException(status_code=400, detail=INVALID_RULE_TYPE_MSG)
    
    try:
        success = RuleConfigService.update_rules(tenant_id, rule_type, rules)
        if success:
            # Invalidate cache to force reload
            RuleConfigService.invalidate_cache(tenant_id, rule_type)
            
            logger.info(f"Rules updated for tenant {tenant_id}, rule_type {rule_type}")
            return {
                "status": "success",
                "message": f"{rule_type} rules updated successfully",
                "tenant_id": tenant_id,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update rules")
    except Exception as e:
        logger.error(f"Failed to update rules for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update rules: {str(e)}")


@router.post("/rules/{rule_type}/upload")
async def upload_rules_file(
    rule_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """
    Upload a JSON rules file for the tenant.
    
    Args:
        rule_type: "technical" or "medical"
        file: JSON file containing rule configuration
    """
    if rule_type not in VALID_RULE_TYPES:
        raise HTTPException(status_code=400, detail=INVALID_RULE_TYPE_MSG)
    
    if not file.filename or not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be a JSON file")
    
    try:
        # Read and parse JSON file
        content = await file.read()
        rules = json.loads(content.decode('utf-8'))
        
        # Validate JSON structure (basic validation)
        if not isinstance(rules, dict):
            raise HTTPException(status_code=400, detail="Rules must be a JSON object")
        
        # Update rules
        success = RuleConfigService.update_rules(tenant_id, rule_type, rules)
        if success:
            RuleConfigService.invalidate_cache(tenant_id, rule_type)
            
            logger.info(f"Rules file uploaded for tenant {tenant_id}, rule_type {rule_type}")
            return {
                "status": "success",
                "message": f"{rule_type} rules uploaded successfully",
                "tenant_id": tenant_id,
                "file_name": file.filename,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save rules")
            
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to upload rules file for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload rules: {str(e)}")


@router.post("/rules/{rule_type}/reload")
async def reload_rules(
    rule_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """
    Force reload rules from file (invalidates cache).
    Useful after manually updating rule files.
    
    Args:
        rule_type: "technical" or "medical"
    """
    if rule_type not in VALID_RULE_TYPES:
        raise HTTPException(status_code=400, detail=INVALID_RULE_TYPE_MSG)
    
    try:
        RuleConfigService.invalidate_cache(tenant_id, rule_type)
        logger.info(f"Rules cache invalidated for tenant {tenant_id}, rule_type {rule_type}")
        return {
            "status": "success",
            "message": f"{rule_type} rules cache invalidated",
            "tenant_id": tenant_id,
        }
    except Exception as e:
        logger.error(f"Failed to reload rules for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload rules: {str(e)}")


@router.get("/rules/{rule_type}/validate")
async def validate_rules(
    rule_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """
    Validate that rules file exists and is properly formatted.
    
    Args:
        rule_type: "technical" or "medical"
    """
    if rule_type not in VALID_RULE_TYPES:
        raise HTTPException(status_code=400, detail=INVALID_RULE_TYPE_MSG)
    
    try:
        rules_path = RuleConfigService.get_rules_path(tenant_id, rule_type)
        exists = rules_path.exists()
        
        if exists:
            rules = RuleConfigService.get_rules(tenant_id, rule_type)
            return {
                "status": "valid",
                "file_path": str(rules_path),
                "exists": True,
                "rule_count": len(rules),
            }
        else:
            return {
                "status": "not_found",
                "file_path": str(rules_path),
                "exists": False,
                "message": "Using default rules",
            }
    except Exception as e:
        logger.error(f"Failed to validate rules for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate rules: {str(e)}")

