# Tenant ID Guide

## What is Tenant ID?

**Tenant ID** is a multi-tenancy identifier that allows the application to support multiple organizations (tenants) within a single database instance. Each tenant's data is isolated from other tenants.

## How Tenant ID Works

### 1. **User Level**
Every user belongs to a tenant:

```python
class User(Base):
    tenant_id = Column(String(50), index=True, nullable=False, default="default")
```

When a user signs up, they're assigned to a tenant (default: `"default"`).

### 2. **Data Isolation**
All data is scoped by tenant_id:

- **Claims**: Each claim is tagged with the uploader's tenant_id
- **Rules**: Rule documents are stored per tenant
- **Analytics**: Metrics are aggregated per tenant
- **Vector Store**: Embeddings are isolated per tenant

### 3. **Automatic Tenant Resolution**

When a user makes an API request:

```python
# 1. User authenticates → JWT token contains username
# 2. get_current_user() fetches User from database
# 3. get_current_tenant() extracts tenant_id from User.tenant_id
# 4. All operations use that tenant_id
```

## Tenant ID Examples

### Default Setup (Single Tenant)
```env
DEFAULT_TENANT=default
```

All users get `tenant_id = "default"`. All data belongs to one organization.

### Multi-Tenant Setup

**Option 1: Per Organization**
```python
# Organization A
tenant_id = "org_acme_healthcare"

# Organization B  
tenant_id = "org_global_insurance"
```

**Option 2: Per Region**
```python
# UAE Region
tenant_id = "region_uae"

# Saudi Region
tenant_id = "region_ksa"
```

**Option 3: Custom Tenant Assignment**
```python
# During user signup, assign tenant based on:
# - Organization selection
# - Email domain
# - Invitation code
```

## Database Schema

All tables include `tenant_id`:

```python
# Users table
users.tenant_id = "default"  # User's organization

# Claims table
claims_master.tenant_id = "default"  # Tenant who uploaded

# Rules table
rule_documents.tenant_id = "default"  # Tenant-specific rules

# Metrics table
validation_metrics.tenant_id = "default"  # Per-tenant analytics
```

## How to Use Tenant ID

### 1. **Get Current Tenant**

```python
from dependencies import get_current_tenant

@router.get("/claims")
async def get_claims(
    tenant_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    # tenant_id is automatically extracted from logged-in user
    claims = db.query(ClaimMaster).filter(
        ClaimMaster.tenant_id == tenant_id
    ).all()
    return claims
```

### 2. **Create Tenant-Specific Data**

```python
# Claims automatically get tenant_id from user
claim = ClaimMaster(
    claim_id="CLM-001",
    tenant_id=tenant_id,  # From get_current_tenant()
    # ...
)
```

### 3. **Query with Tenant Filter**

```python
# Always filter by tenant_id to ensure data isolation
claims = db.query(ClaimMaster).filter(
    ClaimMaster.tenant_id == tenant_id
).all()
```

### 4. **Vector Store per Tenant**

```python
# Each tenant has their own collection
vector_store = VectorStore(tenant_id="org_acme")
# Creates collection: "rules_org_acme"

vector_store = VectorStore(tenant_id="org_global")
# Creates collection: "rules_org_global"
```

## Setting Up Multi-Tenancy

### Option 1: Environment Variable (Simple)

All users use the same tenant:

```env
DEFAULT_TENANT=my_company
```

### Option 2: User Signup with Tenant Selection

Modify signup endpoint:

```python
@router.post("/signup")
async def signup(
    user_data: SignUpRequest,
    organization_code: str,  # New field
    db: Session = Depends(get_db),
):
    # Validate organization code
    tenant_id = f"org_{organization_code}"
    
    user = User(
        username=user_data.username,
        tenant_id=tenant_id,  # Custom tenant
        # ...
    )
```

### Option 3: Superuser Tenant Assignment

Add admin endpoint:

```python
@router.post("/admin/assign-tenant")
async def assign_tenant(
    user_id: int,
    new_tenant_id: str,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(403, "Admin only")
    
    user = db.query(User).filter(User.id == user_id).first()
    user.tenant_id = new_tenant_id
    db.commit()
```

## Best Practices

### ✅ DO:
- Always filter queries by `tenant_id`
- Use `get_current_tenant()` dependency for automatic resolution
- Store tenant_id in all user-created records
- Use meaningful tenant IDs (e.g., `org_acme_healthcare`)

### ❌ DON'T:
- Expose tenant_id in client-side code
- Allow users to change their own tenant_id
- Query data without tenant_id filter
- Use tenant_id from request body (use dependency instead)

## Testing Multi-Tenancy

```python
# Create test users for different tenants
user1 = User(username="alice", tenant_id="tenant_a")
user2 = User(username="bob", tenant_id="tenant_b")

# Upload claims for each
claim1 = ClaimMaster(claim_id="C1", tenant_id="tenant_a")
claim2 = ClaimMaster(claim_id="C2", tenant_id="tenant_b")

# Verify isolation
alice_claims = db.query(ClaimMaster).filter(
    ClaimMaster.tenant_id == "tenant_a"
).all()  # Only returns claim1

bob_claims = db.query(ClaimMaster).filter(
    ClaimMaster.tenant_id == "tenant_b"
).all()  # Only returns claim2
```

## Current Implementation

Currently, the system uses:
- **Default tenant**: `"default"` (from `DEFAULT_TENANT` env var)
- **Auto-assignment**: New users get `tenant_id = settings.DEFAULT_TENANT`
- **Isolation**: All queries filter by `tenant_id`

To customize, modify:
1. `app/config.py`: `DEFAULT_TENANT` setting
2. `app/api/v1/auth.py`: Signup logic
3. `app/dependencies.py`: Tenant resolution logic

