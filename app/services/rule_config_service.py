"""Rule configuration service for dynamic multi-tenant rule management."""
import json
import hashlib
from typing import Dict, Optional
from pathlib import Path
from functools import lru_cache
from utils.logger import get_logger

logger = get_logger(__name__)


class RuleConfigService:
    """
    Manages rule configurations per tenant.
    Supports dynamic rule loading and caching with invalidation.
    """
    
    # In-memory cache: {tenant_id: {rule_type: (rules_dict, file_hash)}}
    _rule_cache: Dict[str, Dict[str, tuple]] = {}
    
    @classmethod
    def get_technical_rules(cls, tenant_id: str) -> Dict:
        """Get technical rules for a tenant, with caching."""
        return cls._get_rules(tenant_id, "technical")
    
    @classmethod
    def get_medical_rules(cls, tenant_id: str) -> Dict:
        """Get medical rules for a tenant, with caching."""
        return cls._get_rules(tenant_id, "medical")
    
    @classmethod
    def get_rules(cls, tenant_id: str, rule_type: str) -> Dict:
        """Public method to get rules (for API use)."""
        return cls._get_rules(tenant_id, rule_type)
    
    @classmethod
    def _get_rules(cls, tenant_id: str, rule_type: str) -> Dict:
        """Load rules with file-based caching and hash validation."""
        # Check cache
        if tenant_id in cls._rule_cache and rule_type in cls._rule_cache[tenant_id]:
            cached_rules, cached_hash = cls._rule_cache[tenant_id][rule_type]
            current_hash = cls._get_file_hash(tenant_id, rule_type)
            
            # If file hasn't changed, return cached rules
            if current_hash == cached_hash:
                return cached_rules
        
        # Load rules from file
        rules_path = cls._get_rules_path(tenant_id, rule_type)
        rules = cls._load_rules_file(rules_path, rule_type)
        
        # Cache the rules
        if tenant_id not in cls._rule_cache:
            cls._rule_cache[tenant_id] = {}
        
        file_hash = cls._get_file_hash(tenant_id, rule_type)
        cls._rule_cache[tenant_id][rule_type] = (rules, file_hash)
        
        logger.info(f"Loaded {rule_type} rules for tenant {tenant_id} from {rules_path}")
        return rules
    
    @classmethod
    def _get_rules_path(cls, tenant_id: str, rule_type: str) -> Path:
        """Get the path to rules file for a tenant."""
        tenant_path = Path(f"app/rules/{tenant_id}/{rule_type}_rules.json")
        default_path = Path(f"app/rules/default/{rule_type}_rules.json")
        
        if tenant_path.exists():
            return tenant_path
        return default_path
    
    @classmethod
    def get_rules_path(cls, tenant_id: str, rule_type: str) -> Path:
        """Public method to get rules path (for API use)."""
        return cls._get_rules_path(tenant_id, rule_type)
    
    @classmethod
    def _load_rules_file(cls, rules_path: Path, rule_type: str) -> Dict:
        """Load rules from JSON file."""
        if not rules_path.exists():
            logger.warning(f"Rules file not found: {rules_path}, using defaults")
            return cls._get_default_rules(rule_type)
        
        try:
            with open(rules_path, 'r') as f:
                rules = json.load(f)
                logger.debug(f"Loaded {rule_type} rules from {rules_path}")
                return rules
        except Exception as e:
            logger.error(f"Failed to load rules from {rules_path}: {e}, using defaults")
            return cls._get_default_rules(rule_type)
    
    @classmethod
    def _get_file_hash(cls, tenant_id: str, rule_type: str) -> Optional[str]:
        """Get hash of rules file for change detection."""
        rules_path = cls._get_rules_path(tenant_id, rule_type)
        if not rules_path.exists():
            return None
        
        try:
            with open(rules_path, 'rb') as f:
                file_content = f.read()
                return hashlib.md5(file_content).hexdigest()
        except Exception:
            return None
    
    @classmethod
    def _get_default_rules(cls, rule_type: str) -> Dict:
        """Get default rules."""
        if rule_type == "technical":
            return {
                "services_requiring_approval": [],
                "diagnoses_requiring_approval": [],
                "paid_amount_threshold": 5000.0,
                "unique_id_pattern": r"^[A-Z0-9-]{10,}$",
                "unique_id_validation": {
                    "description": "unique_id structure validation",
                    "verify_segments": True
                }
            }
        else:  # medical
            return {
                "inpatient_services": [],
                "outpatient_services": [],
                "facility_types": {},
                "facility_registry": {},
                "service_diagnosis_requirements": {},
                "mutually_exclusive_diagnoses": []
            }
    
    @classmethod
    def update_rules(cls, tenant_id: str, rule_type: str, rules: Dict) -> bool:
        """
        Update rules for a tenant by writing to file.
        This will automatically invalidate cache on next access.
        
        Args:
            tenant_id: Tenant identifier
            rule_type: "technical" or "medical"
            rules: Rules dictionary to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure tenant directory exists
            tenant_dir = Path(f"app/rules/{tenant_id}")
            tenant_dir.mkdir(parents=True, exist_ok=True)
            
            rules_path = tenant_dir / f"{rule_type}_rules.json"
            
            # Write rules to file
            with open(rules_path, 'w') as f:
                json.dump(rules, f, indent=2)
            
            # Invalidate cache for this tenant/rule_type
            if tenant_id in cls._rule_cache:
                cls._rule_cache[tenant_id].pop(rule_type, None)
            
            logger.info(f"Updated {rule_type} rules for tenant {tenant_id} at {rules_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update rules for tenant {tenant_id}: {e}")
            return False
    
    @classmethod
    def invalidate_cache(cls, tenant_id: Optional[str] = None, rule_type: Optional[str] = None):
        """
        Invalidate rule cache.
        
        Args:
            tenant_id: If provided, invalidate only this tenant's cache
            rule_type: If provided, invalidate only this rule type
        """
        if tenant_id:
            if rule_type:
                if tenant_id in cls._rule_cache:
                    cls._rule_cache[tenant_id].pop(rule_type, None)
            else:
                cls._rule_cache.pop(tenant_id, None)
        else:
            cls._rule_cache.clear()
        
        logger.info(f"Invalidated cache for tenant={tenant_id}, rule_type={rule_type}")

