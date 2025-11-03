# Multi-Tenant Rule Configuration Guide

## Overview

The system supports **dynamic, multi-tenant rule configuration** that allows switching rule sets without code changes. Each tenant can have their own technical and medical rules, which can be updated at runtime via API or file system.

## Architecture

### 1. Rule Configuration Service (`RuleConfigService`)

Centralized service that manages rule loading, caching, and updates:

- **File-based storage**: Rules stored in `app/rules/{tenant_id}/technical_rules.json` and `app/rules/{tenant_id}/medical_rules.json`
- **Automatic fallback**: If tenant-specific rules don't exist, falls back to `app/rules/default/`
- **Smart caching**: Rules are cached in memory with file hash validation for automatic invalidation
- **Dynamic updates**: Update rules via API or file system changes

### 2. Rule Engines

Both `TechnicalRulesEngine` and `MedicalRulesEngine` use lazy loading:

- Rules are loaded on first access via `RuleConfigService`
- Cache is automatically invalidated when files change (detected by hash)
- Supports manual reload via `reload_rules()` method

## Usage

### Option 1: File System (Manual)

1. **Create tenant-specific rules directory:**
   ```bash
   mkdir -p app/rules/tenant_acme
   ```

2. **Create rule files:**
   ```bash
   # Copy from default
   cp app/rules/default/technical_rules.json app/rules/tenant_acme/
   cp app/rules/default/medical_rules.json app/rules/tenant_acme/
   
   # Edit as needed
   ```

3. **Update rules:**
   - Edit JSON files directly
   - System automatically detects changes on next access (hash-based)
   - Or call `/api/v1/rules/{rule_type}/reload` to force refresh

### Option 2: API (Programmatic)

#### Get Current Rules

```bash
# Get all rules
GET /api/v1/rules

# Get specific rule type
GET /api/v1/rules?rule_type=technical
GET /api/v1/rules?rule_type=medical
```

#### Update Rules

```bash
# Update via JSON body
PUT /api/v1/rules/technical
Content-Type: application/json

{
  "services_requiring_approval": ["SRV1001", "SRV1002"],
  "diagnoses_requiring_approval": ["E11.9"],
  "paid_amount_threshold": 1000.0,
  "unique_id_pattern": "^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$"
}
```

#### Upload Rules File

```bash
# Upload JSON file
POST /api/v1/rules/technical/upload
Content-Type: multipart/form-data

file: technical_rules.json
```

#### Reload Rules

```bash
# Force reload from file (invalidates cache)
POST /api/v1/rules/technical/reload
```

#### Validate Rules

```bash
# Check if rules file exists and is valid
GET /api/v1/rules/technical/validate
```

## Rule Structure

### Technical Rules (`technical_rules.json`)

```json
{
  "services_requiring_approval": ["SRV1001", "SRV1002", "SRV2008"],
  "diagnoses_requiring_approval": ["E11.9", "R07.9", "Z34.0"],
  "paid_amount_threshold": 250.0,
  "unique_id_pattern": "^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$",
  "unique_id_validation": {
    "description": "unique_id structure: first4(National ID) – middle4(Member ID) – last4(Facility ID)",
    "verify_segments": true
  }
}
```

### Medical Rules (`medical_rules.json`)

```json
{
  "inpatient_services": ["SRV1001", "SRV1002", "SRV1003"],
  "outpatient_services": ["SRV2001", "SRV2002", "SRV2007"],
  "facility_types": {
    "MATERNITY_HOSPITAL": ["SRV2008"],
    "DIALYSIS_CENTER": ["SRV1003", "SRV2010"],
    "CARDIOLOGY_CENTER": ["SRV2001", "SRV2011"],
    "GENERAL_HOSPITAL": ["SRV1001", "SRV2001", "SRV2007"]
  },
  "facility_registry": {
    "96GUDLMT": "GENERAL_HOSPITAL",
    "2XKSZK4T": "MATERNITY_HOSPITAL"
  },
  "service_diagnosis_requirements": {
    "SRV2007": ["E11.9"],
    "SRV2006": ["J45.909"]
  },
  "mutually_exclusive_diagnoses": [
    {
      "diagnoses": ["R73.03", "E11.9"],
      "reason": "Prediabetes cannot coexist with Diabetes Mellitus"
    }
  ]
}
```

## Configuration Examples

### Example 1: Different Thresholds Per Tenant

**Tenant A (`tenant_acme`):**
```json
{
  "paid_amount_threshold": 500.0
}
```

**Tenant B (`tenant_global`):**
```json
{
  "paid_amount_threshold": 5000.0
}
```

### Example 2: Different Service Lists

**Tenant A:**
```json
{
  "inpatient_services": ["SRV1001", "SRV1002"],
  "outpatient_services": ["SRV2001", "SRV2002"]
}
```

**Tenant B:**
```json
{
  "inpatient_services": ["SRV1001", "SRV1002", "SRV1003", "SRV1004"],
  "outpatient_services": ["SRV2001", "SRV2002", "SRV2003", "SRV2004", "SRV2005"]
}
```

## Caching & Performance

- **Automatic cache invalidation**: File changes detected via MD5 hash
- **Lazy loading**: Rules loaded only when needed
- **In-memory cache**: Reduces file I/O for frequently accessed tenants
- **Manual cache control**: `POST /api/v1/rules/{rule_type}/reload` to force refresh

## Best Practices

1. **Version Control**: Keep rule files in version control for audit trail
2. **Backup**: Always backup existing rules before updates
3. **Validation**: Use `/validate` endpoint to check rules before production
4. **Testing**: Test rule changes with sample claims before deploying
5. **Documentation**: Document tenant-specific rule customizations

## Migration from Default Rules

To migrate a tenant from default to custom rules:

```bash
# 1. Create tenant directory
mkdir -p app/rules/tenant_acme

# 2. Copy default rules
cp app/rules/default/technical_rules.json app/rules/tenant_acme/
cp app/rules/default/medical_rules.json app/rules/tenant_acme/

# 3. Customize as needed
# Edit the JSON files

# 4. Reload (optional, will auto-detect on next access)
curl -X POST http://localhost:8000/api/v1/rules/technical/reload \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## API Authentication

All rule management endpoints require authentication:
- User must be logged in (JWT token)
- Tenant is automatically determined from user's `tenant_id`
- Users can only manage rules for their own tenant

## Error Handling

- Invalid JSON: Returns 400 with error details
- Missing file: Falls back to default rules
- Invalid rule structure: Logs warning, uses defaults
- Cache errors: Automatically falls back to file loading

