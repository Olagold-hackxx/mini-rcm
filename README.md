# Medical Claims Validator - Production-Grade System

A comprehensive, multi-tenant medical claims validation system built with FastAPI, PostgreSQL, and OpenAI LLM integration. The system performs automated validation of healthcare claims using both rule-based validation and AI-powered analysis.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Multi-Tenancy](#multi-tenancy)
- [Rule Engine](#rule-engine)
- [LLM & RAG Integration](#llm--rag-integration)
- [API Endpoints](#api-endpoints)
- [Frontend Architecture](#frontend-architecture)
- [Database Schema](#database-schema)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Development Guide](#development-guide)

---

## 🎯 Overview

This system validates medical claims through a multi-stage pipeline that combines:
- **Data Quality Validation**: Ensures claim data integrity
- **Technical Rules Validation**: Applies deterministic business rules
- **Medical Rules Validation**: Uses LLM with RAG for complex medical adjudication
- **Analytics & Reporting**: Provides insights into validation results

### Key Features

- ✅ **Multi-tenant Support**: Isolated data and configurations per organization
- ✅ **Dynamic Rule Configuration**: Update rules without code changes
- ✅ **RAG-Powered LLM**: Context-aware claim validation using vector embeddings
- ✅ **Batch Processing**: Process multiple claims files efficiently
- ✅ **Real-time Analytics**: Dashboard with charts and metrics
- ✅ **RESTful API**: Complete API for integrations
- ✅ **Modern Frontend**: Next.js 16 with TypeScript and Tailwind CSS

---

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Dashboard  │  │   Upload    │  │   Results    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                    ┌────────▼────────┐
                    │   FastAPI Backend │
                    │   (REST API)      │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼──────┐  ┌─────────▼─────────┐  ┌──────▼────────┐
│  PostgreSQL  │  │  Validation       │  │  ChromaDB     │
│  Database    │  │  Pipeline         │  │  Vector Store │
└──────────────┘  └─────────┬─────────┘  └───────────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
        ┌───────▼──┐  ┌────▼────┐  ┌──▼────────┐
        │ Rule     │  │ OpenAI  │  │ Static    │
        │ Engine    │  │ LLM API │  │ Validator │
        └───────────┘  └─────────┘  └───────────┘
```

### Validation Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claims Validation Pipeline                     │
└─────────────────────────────────────────────────────────────────┘

Stage 1: INGESTION
├── Parse CSV/Excel file
├── Extract claim data
├── Generate unique claim_ids
└── Insert raw claims into master table

Stage 2: DATA QUALITY VALIDATION
├── Check required fields
├── Validate data types
├── Check for missing values
└── Flag data quality errors

Stage 3: STATIC RULES VALIDATION
├── Technical Rules Engine
│   ├── Service approval requirements
│   ├── Diagnosis approval requirements
│   ├── Paid amount thresholds
│   └── Unique ID format validation
└── Medical Rules Engine (commented out - LLM handles this)

Stage 4: LLM VALIDATION
├── Build RAG queries from claim
├── Retrieve relevant rules from vector store
├── Generate comprehensive prompt
├── Call OpenAI LLM for analysis
├── Parse LLM response
└── Extract validation status and explanations

Stage 5: UPDATE MASTER TABLE
├── Update claim status
├── Store error explanations
├── Store technical/medical errors
└── Set processed timestamp

Stage 6: GENERATE ANALYTICS
├── Calculate metrics
├── Store in validation_metrics table
└── Return summary
```

---

## 🛠️ Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Core language |
| **FastAPI** | Latest | REST API framework |
| **SQLAlchemy** | 2.0+ | ORM for database operations |
| **PostgreSQL** | 14+ | Primary database |
| **Alembic** | Latest | Database migrations |
| **Pydantic** | 2.0+ | Data validation and settings |
| **OpenAI** | Latest | LLM API and embeddings |
| **LangChain** | Latest | LLM orchestration |
| **ChromaDB** | Latest | Vector database for RAG |
| **Pandas** | Latest | Data processing |
| **pypdf** | Latest | PDF parsing for rules |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16+ | React framework |
| **TypeScript** | Latest | Type safety |
| **React** | 18+ | UI library |
| **Tailwind CSS** | Latest | Styling |
| **shadcn/ui** | Latest | UI components |
| **Recharts** | Latest | Data visualization |
| **sonner** | Latest | Toast notifications |
| **react-markdown** | Latest | Markdown rendering |
| **xlsx** | Latest | Excel file parsing |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Local development orchestration |
| **Vercel** | Frontend deployment |
| **PostgreSQL** | Production database |

---

## 🧩 System Components

### 1. Backend API (`app/`)

#### Core Modules

**`config.py`**
- Centralized configuration management
- Environment variable loading
- Settings for database, LLM, RAG, multi-tenancy

**`main.py`**
- FastAPI application entry point
- CORS middleware configuration
- Router registration
- Health check endpoint

**`models/`**
- `database.py`: SQLAlchemy models (User, ClaimMaster, RuleDocument, ValidationMetrics)
- `schemas.py`: Pydantic schemas for API validation

**`db/`**
- `session.py`: Database session management
- `repositories/`: Repository pattern for data access

**`api/v1/`**
- `auth.py`: Authentication endpoints (login, signup, JWT)
- `upload.py`: File upload and processing
- `claims.py`: Claims listing and retrieval
- `analytics.py`: Analytics and metrics endpoints
- `rules.py`: Rule configuration management
- `tenants.py`: Tenant creation and management

**`pipeline/`**
- `orchestrator.py`: Main pipeline coordinator
- `stages/`:
  - `ingestion.py`: File parsing and data extraction
  - `data_quality.py`: Data quality validation
  - `static_validation.py`: Technical rules application
  - `llm_validation.py`: LLM-based validation
- `validators/`:
  - `technical_rules.py`: Technical rules engine
  - `medical_rules.py`: Medical rules engine (static)

**`llm/`**
- `evaluator.py`: LLM evaluation orchestration
- `prompt_templates.py`: Prompt engineering
- `retriever.py`: RAG rule retrieval
- `vector_store.py`: ChromaDB integration
- `embeddings.py`: OpenAI embeddings

**`services/`**
- `rule_config_service.py`: Dynamic rule configuration management

**`utils/`**
- `logger.py`: Logging configuration
- `security.py`: Password hashing, JWT tokens

### 2. Frontend (`frontend/`)

#### Structure

```
frontend/
├── app/
│   ├── (dashboard)/          # Protected dashboard routes
│   │   └── dashboard/
│   │       ├── page.tsx      # Main dashboard
│   │       ├── upload/       # File upload page
│   │       ├── results/      # Results and analytics
│   │       └── settings/     # Settings and configuration
│   ├── login/                # Authentication
│   ├── signup/               # User registration
│   └── page.tsx              # Landing page
├── components/
│   ├── auth/                 # Login/signup forms
│   ├── dashboard/            # Dashboard components
│   ├── results/              # Results table and charts
│   ├── upload/               # File upload components
│   ├── settings/             # Settings components
│   └── ui/                   # Reusable UI components
├── lib/
│   ├── api.ts                # API client
│   └── utils.ts              # Utility functions
└── package.json
```

---

## 🔄 Data Flow

### Complete Request Flow

```
1. User Uploads Claims File (Frontend)
   │
   ├─► POST /api/v1/upload/claims
   │   │
   │   └─► PipelineOrchestrator.process_claims_file()
   │       │
   │       ├─► Stage 1: Ingestion
   │       │   ├─► Parse CSV/Excel
   │       │   ├─► Extract claim data
   │       │   ├─► Generate claim_ids
   │       │   └─► Insert into claims_master (status: "Processing")
   │       │
   │       ├─► Stage 2: Data Quality
   │       │   ├─► Validate required fields
   │       │   ├─► Check data types
   │       │   └─► Flag data quality errors
   │       │
   │       ├─► Stage 3: Static Validation
   │       │   ├─► TechnicalRulesEngine.validate()
   │       │   │   ├─► Check service approval requirements
   │       │   │   ├─► Check diagnosis approval requirements
   │       │   │   ├─► Validate paid amount threshold
   │       │   │   └─► Validate unique ID format
   │       │   └─► Store technical errors and passed rules
   │       │
   │       ├─► Stage 4: LLM Validation
   │       │   ├─► RuleRetriever.retrieve_relevant_rules()
   │       │   │   ├─► Build multiple semantic queries
   │       │   │   ├─► Search ChromaDB vector store
   │       │   │   ├─► Retrieve top-k relevant rules
   │       │   │   └─► Deduplicate and return
   │       │   │
   │       │   ├─► LLMEvaluator.evaluate()
   │       │   │   ├─► Build prompt with claim + rules
   │       │   │   ├─► Call OpenAI API (GPT-4)
   │       │   │   ├─► Parse LLM response
   │       │   │   └─► Extract validation status
   │       │   │
   │       │   └─► Store LLM explanation and errors
   │       │
   │       ├─► Stage 5: Update Master Table
   │       │   ├─► Update claim status
   │       │   ├─► Store error explanations
   │       │   └─► Set processed timestamp
   │       │
   │       └─► Stage 6: Generate Analytics
   │           ├─► Calculate metrics
   │           ├─► Store in validation_metrics
   │           └─► Return summary
   │
   └─► Response: { batch_id, total_claims, validated, not_validated, metrics }
```

### LLM Validation Deep Dive

```
Claim Data
    │
    ▼
RuleRetriever.retrieve_relevant_rules()
    │
    ├─► Build Multiple Queries:
    │   ├─► "service code {service_code} rules requirements"
    │   ├─► "diagnosis code {diagnosis} approval requirements"
    │   ├─► "service {service} diagnosis {diagnosis} requirements"
    │   ├─► "approval requirement prior authorization"
    │   └─► ... (11+ query variations)
    │
    ├─► For each query:
    │   ├─► vector_store.search(query, n_results=30)
    │   ├─► Filter by tenant_id metadata
    │   └─► Collect results
    │
    ├─► Deduplicate by content hash
    │
    └─► Return top 150 rules (TOP_K_RETRIEVAL * 5)
        │
        ▼
LLMEvaluator.evaluate()
    │
    ├─► Build Prompt:
    │   ├─► Claim details
    │   ├─► Retrieved rules (up to 50 shown)
    │   ├─► Validation instructions
    │   └─► Expected output format
    │
    ├─► Call OpenAI API:
    │   ├─► Model: gpt-4.1
    │   ├─► Temperature: 0.0 (deterministic)
    │   ├─► Max tokens: 2000
    │   └─► System + User prompts
    │
    ├─► Parse Response:
    │   ├─► Extract VALIDATION_STATUS
    │   ├─► Extract TECHNICAL_RULES_STATUS
    │   ├─► Extract MEDICAL_RULES_STATUS
    │   ├─► Extract DETAILED_EXPLANATION
    │   └─► Extract RECOMMENDED_ACTION
    │
    └─► Return structured validation result
```

---

## 🏢 Multi-Tenancy

### Architecture

The system implements **data-level multi-tenancy** where each tenant has:
- Isolated database records (filtered by `tenant_id`)
- Separate rule configurations (`app/rules/{tenant_id}/`)
- Independent vector store collections (`rules_{tenant_id}`)
- Isolated analytics and metrics

### Tenant Resolution Flow

```
1. User authenticates → JWT token issued
   │
   ├─► Token contains username
   │
2. API request with JWT
   │
   ├─► get_current_user() dependency
   │   ├─► Decode JWT
   │   ├─► Extract username
   │   └─► Query User from database
   │
3. get_current_tenant() dependency
   │
   ├─► Extract tenant_id from User.tenant_id
   │
4. All operations filtered by tenant_id
   │
   ├─► Database queries: .filter(ClaimMaster.tenant_id == tenant_id)
   ├─► Rule loading: app/rules/{tenant_id}/
   ├─► Vector store: VectorStore(tenant_id)
   └─► Analytics: Filtered by tenant_id
```

### Tenant Management

**Creating a Tenant:**
```
POST /api/v1/tenants/create
{
  "tenant_id": "acme_healthcare",
  "copy_from_default": true
}

→ Creates: app/rules/acme_healthcare/
→ Copies: default rules (optional)
→ Updates: User.tenant_id = "acme_healthcare"
```

**Default Tenant Protection:**
- The "default" tenant is read-only
- Rules cannot be modified via API
- Users must create custom tenants to customize rules

---

## ⚙️ Rule Engine

### Rule Configuration System

The rule engine supports **dynamic rule configuration** without code changes:

```
RuleConfigService (Singleton)
    │
    ├─► File-based storage
    │   └─► app/rules/{tenant_id}/{rule_type}_rules.json
    │
    ├─► Smart caching
    │   ├─► In-memory cache with file hash
    │   ├─► Auto-invalidation on file change
    │   └─► Lazy loading
    │
    └─► API endpoints
        ├─► GET /rules - Get current rules
        ├─► PUT /rules/{type} - Update rules
        ├─► POST /rules/{type}/upload - Upload JSON file
        └─► POST /rules/{type}/reload - Invalidate cache
```

### Technical Rules

**Structure:**
```json
{
  "services_requiring_approval": ["SRV1001", "SRV1002"],
  "diagnoses_requiring_approval": ["E11.9", "R07.9"],
  "paid_amount_threshold": 250.0,
  "unique_id_pattern": "^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$",
  "unique_id_validation": {
    "description": "Format: NID-Member-Facility",
    "verify_segments": true
  }
}
```

**Validation Logic:**
1. **Service Approval Check**: If service_code in `services_requiring_approval`, approval_number must be present
2. **Diagnosis Approval Check**: If diagnosis_code in `diagnoses_requiring_approval`, approval_number must be present
3. **Amount Threshold**: `paid_amount_aed` must be ≤ `paid_amount_threshold`
4. **Unique ID Format**: Must match regex pattern

### Medical Rules

**Structure:**
```json
{
  "inpatient_services": ["SRV1001", "SRV1002"],
  "outpatient_services": ["SRV2001", "SRV2007"],
  "facility_types": {
    "GENERAL_HOSPITAL": ["SRV1001", "SRV2001"],
    "MATERNITY_HOSPITAL": ["SRV2008"]
  },
  "service_diagnosis_requirements": {
    "SRV2007": ["E11.9"],
    "SRV2006": ["J45.909"]
  },
  "mutually_exclusive_diagnoses": [
    {"diagnoses": ["R73.03", "E11.9"], "reason": "..."}
  ]
}
```

**Note:** Medical rules are primarily validated by the LLM using RAG. Static medical rules engine exists but is currently bypassed.

---

## 🤖 LLM & RAG Integration

### RAG (Retrieval Augmented Generation) Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Pipeline                             │
└─────────────────────────────────────────────────────────────┘

1. Rule Documents (PDFs)
   │
   ├─► PDF Parsing (pypdf)
   ├─► Text Extraction
   ├─► Chunking (500 chars, 50 overlap)
   └─► Metadata Assignment
       │
       ▼
2. Embedding Generation
   │
   ├─► OpenAI Embeddings API
   ├─► Model: text-embedding-3-small
   ├─► Dimension: 1536
   └─► Store in ChromaDB
       │
       ▼
3. Vector Store (ChromaDB)
   │
   ├─► Collection: rules_{tenant_id}
   ├─► Documents: Rule chunks
   ├─► Embeddings: Vector representations
   └─► Metadata: {tenant_id, rule_type, chunk_index, source}
       │
       ▼
4. Query Time
   │
   ├─► Claim arrives
   ├─► Build semantic queries
   ├─► Generate query embeddings
   ├─► Search ChromaDB (similarity search)
   ├─► Retrieve top-k relevant rules
   └─► Pass to LLM context
       │
       ▼
5. LLM Evaluation
   │
   ├─► Prompt: Claim + Retrieved Rules
   ├─► OpenAI GPT-4
   ├─► Parse structured response
   └─► Return validation result
```

### Query Building Strategy

The `RuleRetriever` builds **multiple focused queries** to ensure comprehensive rule coverage:

```python
# Example queries for a claim with:
# - service_code: "SRV2007"
# - diagnosis: "E11.9"
# - encounter_type: "OUTPATIENT"

Queries generated:
1. "service code SRV2007 rules requirements eligibility"
2. "service SRV2007 allowed not allowed restrictions"
3. "service code SRV2007 approval authorization required"
4. "service code SRV2007 required diagnosis codes"
5. "what diagnosis codes are required for service SRV2007"
6. "diagnosis code E11.9 requirements approval eligibility"
7. "diagnosis E11.9 authorization prior approval"
8. "service code SRV2007 requires diagnosis code E11.9"
9. "service SRV2007 with diagnosis E11.9 eligibility requirements"
10. "approval requirement prior authorization services diagnoses"
11. "outpatient encounter service eligibility inpatient outpatient"
12. ... (fallback general queries)
```

### Prompt Engineering

The LLM prompt is carefully structured to ensure accurate validation:

```
1. SYSTEM CONTEXT
   - Role: Medical claims validator
   - Instructions: Strict adherence to provided rules

2. CLAIM DATA
   - All claim fields formatted clearly
   - Service codes, diagnoses, encounter types highlighted

3. RETRIEVED RULES (up to 50)
   - Each rule shown with metadata
   - Rules numbered for reference

4. VALIDATION INSTRUCTIONS
   - Check service-diagnosis requirements FIRST
   - Check approval requirements
   - Check encounter type eligibility
   - Check mutually exclusive diagnoses
   - Explicit PASS/FAIL for each rule

5. OUTPUT FORMAT
   - Structured JSON-like format
   - VALIDATION_STATUS: TECHNICAL/MEDICAL/OVERALL
   - DETAILED_EXPLANATION: Markdown formatted
   - RECOMMENDED_ACTION: Actionable steps
```

---

## 🔌 API Endpoints

### Authentication

```
POST   /api/v1/auth/login          # Login (JWT token)
POST   /api/v1/auth/signup         # User registration
GET    /api/v1/auth/me             # Current user info
```

### File Upload & Processing

```
POST   /api/v1/upload/claims       # Upload claims file
       Body: multipart/form-data (file)
       Response: { batch_id, total_claims, metrics }
```

### Claims

```
GET    /api/v1/claims              # List claims (paginated, filtered)
       Query: ?skip=0&limit=100&status=Validated&batch_id=...
GET    /api/v1/claims/{claim_id}  # Get specific claim
```

### Analytics

```
GET    /api/v1/analytics/metrics           # Get metrics summary
GET    /api/v1/analytics/charts/error-breakdown  # Error breakdown chart data
GET    /api/v1/analytics/charts/amount-breakdown  # Amount breakdown chart data
GET    /api/v1/analytics/batches           # List all batches
```

### Rules Management

```
GET    /api/v1/rules                    # Get current rules
       Query: ?rule_type=technical
PUT    /api/v1/rules/{rule_type}        # Update rules
POST   /api/v1/rules/{rule_type}/upload # Upload rules JSON file
POST   /api/v1/rules/{rule_type}/reload # Reload from file
GET    /api/v1/rules/{rule_type}/validate  # Validate rules file
```

### Tenant Management

```
POST   /api/v1/tenants/create      # Create new tenant
POST   /api/v1/tenants/switch      # Switch tenant
GET    /api/v1/tenants/current     # Get current tenant info
GET    /api/v1/tenants/list        # List all tenants
```

### Health

```
GET    /health                      # Health check
GET    /                            # API info
```

---

## 🎨 Frontend Architecture

### Component Structure

```
App Layout
├── Landing Page (/)
│   ├── HeroSection
│   ├── FeaturesSection
│   └── CTASection
│
├── Authentication
│   ├── LoginForm (/login)
│   └── SignupForm (/signup)
│
└── Dashboard (Protected)
    ├── DashboardHeader
    │   ├── User info
    │   └── Tenant display
    │
    ├── Main Dashboard (/dashboard)
    │   ├── StatsCards
    │   ├── QuickActions
    │   └── RecentActivity
    │
    ├── Upload Page (/dashboard/upload)
    │   ├── FileUploadZone
    │   ├── FilePreview
    │   └── UploadForm
    │
    ├── Results Page (/dashboard/results)
    │   ├── BatchSelector
    │   ├── ResultsCharts
    │   │   ├── ErrorBreakdownChart
    │   │   └── AmountBreakdownChart
    │   └── ResultsTable
    │       └── Claim details modal
    │
    └── Settings Page (/dashboard/settings)
        ├── TenantManagement
        │   ├── Create tenant
        │   └── Switch tenant
        └── RulesManagement
            ├── Technical rules editor
            └── Medical rules editor
```

### State Management

- **Local State**: React hooks (`useState`, `useEffect`)
- **API State**: Custom hooks with error handling
- **Auth State**: JWT token in `localStorage`
- **Tenant Context**: Derived from user's `tenant_id`

### API Client

The `lib/api.ts` provides a centralized API client:

```typescript
// Automatic token management
// 401 handling with auto-redirect
// Error formatting
// Type-safe responses

authApi.login(username, password)
uploadApi.uploadClaimsFile(file)
claimsApi.listClaims(params)
analyticsApi.getMetrics(batchId)
rulesApi.getRules(ruleType)
tenantsApi.createTenant(tenantId)
```

---

## 🗄️ Database Schema

### Tables

#### `users`
```sql
id                  INTEGER PRIMARY KEY
username            VARCHAR(50) UNIQUE
email               VARCHAR(100) UNIQUE
hashed_password     VARCHAR(255)
full_name           VARCHAR(100)
tenant_id           VARCHAR(50) DEFAULT 'default'
is_active           BOOLEAN DEFAULT true
is_superuser        BOOLEAN DEFAULT false
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

#### `claims_master`
```sql
id                      INTEGER PRIMARY KEY
claim_id                VARCHAR(50) UNIQUE
encounter_type          VARCHAR(20)
service_date            TIMESTAMP
national_id             VARCHAR(20)
member_id               VARCHAR(20)
facility_id             VARCHAR(20)
unique_id               VARCHAR(50)
diagnosis_codes         ARRAY[VARCHAR]
service_code            VARCHAR(20)
paid_amount_aed         NUMERIC
approval_number         VARCHAR(50)
status                  VARCHAR(20)  -- 'Validated' | 'Not validated' | 'Processing'
error_type              VARCHAR(50)   -- 'No error' | 'Technical error' | 'Medical error' | 'Both'
error_explanation       TEXT
recommended_action      TEXT
technical_errors        JSON
medical_errors          JSON
data_quality_errors     JSON
llm_evaluated           BOOLEAN
llm_confidence_score    NUMERIC
llm_explanation         TEXT
llm_retrieved_rules     JSON
tenant_id               VARCHAR(50)
batch_id                VARCHAR(50)
uploaded_by             VARCHAR(50)
uploaded_at             TIMESTAMP
processed_at            TIMESTAMP
created_at              TIMESTAMP
updated_at              TIMESTAMP
```

#### `rule_documents`
```sql
id              INTEGER PRIMARY KEY
tenant_id       VARCHAR(50)
rule_type       VARCHAR(20)
content         TEXT
embedding_id    VARCHAR(100)
version         VARCHAR(20)
created_at      TIMESTAMP
```

#### `validation_metrics`
```sql
id                      INTEGER PRIMARY KEY
tenant_id               VARCHAR(50)
batch_id                VARCHAR(50)
total_claims            INTEGER
validated_claims        INTEGER
not_validated_claims    INTEGER
no_error_count          INTEGER
technical_error_count   INTEGER
medical_error_count     INTEGER
both_errors_count       INTEGER
total_paid_amount       NUMERIC
validated_amount        NUMERIC
rejected_amount         NUMERIC
created_at              TIMESTAMP
```

### Indexes

- `users.username`, `users.email`, `users.tenant_id`
- `claims_master.claim_id`, `claims_master.tenant_id`, `claims_master.batch_id`, `claims_master.status`
- `rule_documents.tenant_id`
- `validation_metrics.tenant_id`, `validation_metrics.batch_id`

---

## 🚀 Deployment

### Docker Deployment

**Dockerfile:**
- Base: `python:3.11-slim`
- Installs dependencies from `requirements.txt`
- Copies application code
- Sets up entrypoint script
- Exposes port 8000

**docker-compose.yml:**
```yaml
services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: claims_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  backend:
    build: .
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/claims_db
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      LOAD_RULES: "true"
      RUN_MIGRATIONS: "true"
    depends_on:
      - db
    ports:
      - "8000:8000"
```

**Entrypoint Script (`docker-entrypoint.sh`):**
1. Wait for PostgreSQL
2. Run Alembic migrations
3. Load rules into vector store (if `LOAD_RULES=true`)
4. Start FastAPI server

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/claims_db

# Authentication
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=720

# OpenAI
OPENAI_API_KEY=sk-...

# RAG
USE_RAG=true
EMBEDDING_MODEL=text-embedding-3-small
VECTOR_STORE_PATH=./vector_store/chroma_db
TOP_K_RETRIEVAL=30

# Multi-tenant
DEFAULT_TENANT=default

# Docker
LOAD_RULES=true
RUN_MIGRATIONS=true
TENANT_ID=default
```

### Frontend Deployment (Vercel)

1. Connect GitHub repository
2. Set environment variables:
   - `NEXT_PUBLIC_API_URL`: Backend API URL
3. Deploy automatically on push

---

## ⚙️ Configuration

### Backend Configuration (`app/config.py`)

All settings are environment-based:

```python
class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Medical Claims Validator"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    
    # Authentication
    SECRET_KEY: str  # Required
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720  # 12 hours
    
    # LLM
    OPENAI_API_KEY: str
    LLM_MODEL: str = "gpt-4.1"
    LLM_MAX_TOKENS: int = 2000
    
    # RAG
    USE_RAG: bool = True
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    VECTOR_STORE_PATH: str = "./vector_store/chroma_db"
    TOP_K_RETRIEVAL: int = 30
    
    # Multi-tenant
    DEFAULT_TENANT: str = "default"
```

### Rule Configuration

Rules are stored in JSON files:
- `app/rules/{tenant_id}/technical_rules.json`
- `app/rules/{tenant_id}/medical_rules.json`

Default fallback:
- `app/rules/default/technical_rules.json`
- `app/rules/default/medical_rules.json`

---

## 👨‍💻 Development Guide

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- OpenAI API key

### Backend Setup

```bash
# Clone repository
cd app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/claims_db"
export SECRET_KEY="your-secret-key"
export OPENAI_API_KEY="sk-..."

# Run migrations
alembic upgrade head

# Load rules into vector store
python scripts/load_rules_example.py default

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Start development server
npm run dev
```

### Running Tests

```bash
# Backend tests
pytest

# Frontend tests
npm test
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Loading Rules into Vector Store

```bash
# For default tenant
python scripts/load_rules_example.py default

# For custom tenant
python scripts/load_rules_example.py acme_healthcare
```

---

## 📚 Key Design Decisions

### 1. Multi-Stage Pipeline

**Why:** Separates concerns and allows for easy debugging and optimization of each stage.

### 2. RAG for Medical Rules

**Why:** Medical rules are complex and context-dependent. RAG allows the LLM to access relevant rules dynamically rather than hardcoding all logic.

### 3. File-Based Rule Configuration

**Why:** 
- No database dependency for rules
- Easy version control (git)
- No code changes required
- Supports multiple tenants naturally

### 4. Tenant Isolation

**Why:** 
- Supports multiple organizations
- Data security and privacy
- Customizable rules per tenant
- Scalable architecture

### 5. Batch Processing

**Why:** 
- Efficient processing of multiple claims
- Grouped analytics and reporting
- Easy tracking of upload sources

### 6. LLM + Static Rules Hybrid

**Why:** 
- Static rules for deterministic validation (fast, reliable)
- LLM for complex medical logic (flexible, context-aware)
- Best of both worlds

---

## 🔒 Security Considerations

1. **JWT Authentication**: Secure token-based auth
2. **Password Hashing**: bcrypt with salt
3. **Tenant Isolation**: All queries filtered by tenant_id
4. **Input Validation**: Pydantic schemas for all inputs
5. **CORS**: Configurable for production
6. **Environment Variables**: Sensitive data in .env

---

## 📊 Performance Considerations

1. **Caching**: Rule configuration cached in memory
2. **Batch Processing**: Process claims in batches
3. **Vector Store**: ChromaDB for fast similarity search
4. **Database Indexes**: On tenant_id, batch_id, claim_id
5. **Connection Pooling**: SQLAlchemy connection pool
6. **Lazy Loading**: Rules loaded on-demand

---

## 🎯 Top Five Assumptions

The following assumptions are critical to the system's design and operation:

### (a) LLM enhances explanations but does not override deterministic static rules.
- **Rationale**: Static validation rules (technical rules engine) provide deterministic, reliable validation for business-critical checks (approvals, thresholds, formats). The LLM serves as an enhancement layer for medical validation and explanations, but cannot bypass or override static rule failures.
- **Implementation**: Technical validation errors from static rules always prevent "Validated" status, even if LLM says technical passed.

### (b) RAG retrieval (top-k=30-150) ensures rule context integrity.
- **Rationale**: The system retrieves comprehensive rule context (up to 150 rules via multiple queries) to provide the LLM with sufficient information for accurate medical validation. Incomplete rule retrieval would lead to incorrect validations.
- **Implementation**: Multi-query strategy with 11+ query variations per claim, deduplication, and fallback searches ensure comprehensive coverage.

### (c) Claims adhere to the expected schema; malformed data triggers validation errors.
- **Rationale**: Input data is expected to follow a specific schema (CSV/Excel columns). Data quality validation stage catches schema violations early, preventing downstream processing errors.
- **Implementation**: Data quality stage validates required fields, data types, and format compliance before rule validation.

### (d) OpenAI API availability and rate limits are managed for production use.
- **Rationale**: LLM validation depends on OpenAI API availability. The system assumes API access is reliable, rate limits are configured appropriately, and fallback strategies exist for API failures.
- **Implementation**: Error handling in LLM evaluator, API key validation, and graceful degradation when LLM is unavailable.

### (e) Rule documents (PDFs) are authoritative and complete sources of validation rules.
- **Rationale**: The system extracts and uses rules from PDF documents via RAG. It assumes these documents contain all necessary validation rules and are kept up-to-date. Missing or outdated rules in documents will result in incorrect validations.
- **Implementation**: Rule loading script parses PDFs, vector store indexing ensures rules are searchable, and rule update mechanisms allow document refresh.

---

## 🔍 Additional Important Assumptions

### Medical Coding Standards
- **Assumption**: Medical codes (diagnosis codes like E11.9, service codes like SRV2007) follow standard formats (ICD-10, CPT, or custom coding schemes) and are correctly applied in claims.
- **Impact**: Incorrect or non-standard codes may not be recognized by rule validation.

### Data Privacy and Compliance
- **Assumption**: PHI (Protected Health Information) in claims is handled according to healthcare data privacy regulations (HIPAA, GDPR, etc.). The system assumes proper data encryption, access controls, and audit logging are in place.
- **Impact**: Security breaches could expose sensitive patient data.

### Validation Performance
- **Assumption**: LLM validation latency (typically 2-5 seconds per claim) is acceptable for batch processing workflows. Real-time validation requirements may need optimization.
- **Impact**: High-volume claims processing may require batching or asynchronous processing.

### Rule Consistency
- **Assumption**: Rule documents and JSON rule files are consistent with each other. No conflicts between static rules (JSON) and medical rules (PDFs) for the same validation criteria.
- **Impact**: Conflicting rules could lead to inconsistent validation results.

### User Workflow
- **Assumption**: Users upload claims files, review results, and take corrective actions based on validation feedback. The system assumes users understand error explanations and can act on recommendations.
- **Impact**: Poor user experience or unclear explanations reduce system effectiveness.

### Multi-Tenant Data Isolation
- **Assumption**: Tenant isolation through database filters and vector store collections is sufficient to prevent data leakage between tenants. No cross-tenant data access is possible.
- **Impact**: Data leakage could violate privacy and regulatory requirements.

### Rule Versioning and Auditability
- **Assumption**: Rule changes are tracked (via file system or version control), and validation results can be audited to determine which rule version was applied. Historical rule changes don't need to be preserved in the system.
- **Impact**: Compliance audits may require rule version history.

### Batch Processing Atomicity
- **Assumption**: Claims within a batch are processed independently. Failure of one claim does not affect others in the same batch. No transaction rollback across claims.
- **Impact**: Partial batch failures require manual review and reprocessing.

### LLM Response Reliability
- **Assumption**: OpenAI GPT-4 provides consistent, structured responses that can be reliably parsed. Prompt engineering ensures the LLM follows expected output formats.
- **Impact**: Unparseable LLM responses could cause validation failures or incorrect status assignments.

---

## 🐛 Troubleshooting

### Common Issues

**Issue:** "Collection expecting embedding with dimension of 384, got 1536"
- **Solution:** Delete `vector_store/chroma_db` and reload rules

**Issue:** Rules not found during validation
- **Check:** Rules loaded? Tenant ID matches? Vector store path correct?

**Issue:** LLM validation always returns "VALID"
- **Check:** Prompt structure, retrieved rules, LLM response parsing

**Issue:** Duplicate claim_id errors
- **Solution:** System auto-generates unique IDs, but check for existing claims

---

## 📝 License

[Add your license here]

---

## 🤝 Contributing

[Add contribution guidelines]

---

## 📧 Contact

[Add contact information]

