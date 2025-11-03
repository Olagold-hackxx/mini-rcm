# Frontend-Backend Integration Guide

## Overview

The frontend (Next.js) is now fully integrated with the backend (FastAPI). All components are connected to real API endpoints.

## Setup

### 1. Backend Setup

```bash
cd app
# Create virtual environment if not exists
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database URL, API keys, etc.

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local
# Edit .env.local - set NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Integration

### Authentication
- **Login**: `/api/v1/login` - POST with username/password
- **Signup**: `/api/v1/signup` - POST with user data
- **Get Current User**: `/api/v1/me` - GET (requires auth)

### File Upload
- **Upload Claims**: `/api/v1/upload/claims` - POST multipart/form-data

### Analytics
- **Get Metrics**: `/api/v1/analytics/metrics` - GET
- **Error Breakdown Chart**: `/api/v1/analytics/charts/error-breakdown` - GET
- **Amount Breakdown Chart**: `/api/v1/analytics/charts/amount-breakdown` - GET

### Claims
- **List Claims**: `/api/v1/claims` - GET (supports pagination, filtering, search)
- **Get Claim**: `/api/v1/claims/{claim_id}` - GET

## Features Integrated

### ✅ Dashboard
- Real-time stats cards showing total claims, validated, errors, validation rate
- Connected to analytics API

### ✅ Upload Page
- File upload integrated with backend
- Automatic redirect to results after successful upload
- Error handling

### ✅ Results Page
- **Charts**: 
  - Error breakdown bar chart (counts by error type)
  - Amount breakdown bar chart (AED amounts by error type)
  - Waterfall chart showing validation flow
- **Table**: 
  - Paginated claims list with search
  - Filter by status/error type
  - View detailed claim information in modal

### ✅ Authentication
- Login form connected to backend
- JWT token stored in localStorage
- Token automatically included in API requests

## Environment Variables

### Backend (.env)
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost:5432/claims_db
ANTHROPIC_API_KEY=your-api-key  # Optional
OPENAI_API_KEY=your-api-key     # Optional
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Usage Flow

1. **Login**: User logs in via `/login` page
2. **Upload**: Upload claims file via `/dashboard/upload`
3. **Processing**: Backend processes file through validation pipeline
4. **Results**: View results in `/dashboard/results` with:
   - Summary metrics
   - Charts (error breakdown, amount breakdown, waterfall)
   - Detailed claims table
5. **Dashboard**: View overall statistics on `/dashboard`

## Testing

### Create Test User
```bash
# Use signup endpoint or create directly in database
curl -X POST http://localhost:8000/api/v1/signup \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}'
```

### Upload Test File
```bash
curl -X POST http://localhost:8000/api/v1/upload/claims \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@path/to/claims.xlsx"
```

## Troubleshooting

### CORS Issues
- Backend CORS is configured to allow all origins in development
- For production, update `allow_origins` in `app/main.py`

### Authentication Issues
- Check that token is stored in localStorage
- Verify token format: `Bearer <token>`
- Token expires after 30 minutes (configurable)

### API Connection Issues
- Verify backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in frontend `.env.local`
- Check browser console for API errors

### Database Issues
- Ensure PostgreSQL is running
- Run migrations: `alembic upgrade head`
- Check database connection string in backend `.env`

## Next Steps

1. Add error boundaries for better error handling
2. Implement toast notifications instead of alerts
3. Add loading skeletons for better UX
4. Implement pagination controls in claims table
5. Add export functionality for results
6. Implement real-time updates using WebSockets or polling

