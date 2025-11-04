# Render Deployment Guide

This guide explains how to deploy the Medical Claims Validator application to Render.

## Overview

Render automatically deploys from your Git repository. This CI/CD setup focuses on:
- **Testing & Validation**: Run tests on pull requests and pushes
- **Build Validation**: Ensure code builds successfully
- **Quality Checks**: Linting and type checking

## Render Setup

### Backend Service

1. **Create Web Service**
   - Connect your GitHub repository
   - Select branch: `main`
   - Root Directory: `app/`
   - Build Command: `pip install -r requirements.txt && alembic upgrade head`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **Environment Variables**
   ```
   DATABASE_URL=<from PostgreSQL service>
   SECRET_KEY=<generate a secure key>
   OPENAI_API_KEY=<your OpenAI API key>
   ACCESS_TOKEN_EXPIRE_MINUTES=720
   USE_RAG=true
   EMBEDDING_MODEL=text-embedding-3-small
   DEFAULT_TENANT=default
   LOAD_RULES=true
   RUN_MIGRATIONS=true
   TENANT_ID=default
   ```

3. **PostgreSQL Database**
   - Create PostgreSQL service in Render
   - Copy connection string to `DATABASE_URL`
   - Migrations run automatically on deploy

4. **Vector Store**
   - ChromaDB stores data in `app/vector_store/chroma_db/`
   - Persists between deployments if using Render disk
   - Or use external storage (S3, etc.)

### Frontend Service

1. **Create Static Site**
   - Connect your GitHub repository
   - Root Directory: `frontend/`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `frontend/.next`

2. **Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-service.onrender.com/api/v1
   ```

## CI/CD Workflows

### CI Workflow (`.github/workflows/ci.yml`)

Runs on every push and pull request:
- **Backend Tests**: Unit and integration tests
- **Frontend Build**: Validates Next.js build
- **Linting**: Code quality checks
- **Coverage**: Test coverage reports

### Validate Workflow (`.github/workflows/validate.yml`)

Runs on pull requests:
- **Build Validation**: Ensures code compiles
- **Import Checks**: Validates Python imports
- **Type Checking**: TypeScript validation

## Deployment Process

1. **Push to Main Branch**
   - Render automatically detects changes
   - Runs build command
   - Deploys new version

2. **Database Migrations**
   - Alembic migrations run automatically
   - Check logs for migration status

3. **Rule Loading**
   - If `LOAD_RULES=true`, rules load on startup
   - Check logs for vector store initialization

4. **Health Check**
   - Render monitors `/health` endpoint
   - Automatic restarts on failure

## Monitoring

### Backend Logs
```bash
# View logs in Render dashboard
# Or via CLI:
render logs <service-name>
```

### Health Endpoint
```bash
curl https://your-backend.onrender.com/health
# Should return: {"status": "healthy"}
```

### Database Status
- Check Render PostgreSQL dashboard
- Verify connection in service logs

## Troubleshooting

### Build Fails
- Check build logs in Render dashboard
- Verify all dependencies in `requirements.txt`
- Ensure Python version matches (3.11+)

### Database Connection Issues
- Verify `DATABASE_URL` is correct
- Check PostgreSQL service is running
- Ensure migrations ran successfully

### Vector Store Issues
- Check `LOAD_RULES` environment variable
- Verify `OPENAI_API_KEY` is set
- Check vector store directory permissions

### Frontend Build Issues
- Verify `NEXT_PUBLIC_API_URL` is set
- Check Node.js version (18+)
- Review build logs for errors

## Environment-Specific Configuration

### Development
- Use local PostgreSQL
- Local vector store
- Development API keys

### Production (Render)
- Render PostgreSQL
- Persistent vector store
- Production API keys
- HTTPS enabled

## Rollback

If deployment fails:
1. Go to Render dashboard
2. Select service
3. Click "Manual Deploy"
4. Select previous successful commit
5. Deploy

## Security Checklist

- [ ] `SECRET_KEY` is strong and unique
- [ ] `OPENAI_API_KEY` is stored securely
- [ ] Database credentials are secure
- [ ] CORS is configured for production
- [ ] HTTPS is enabled
- [ ] Environment variables are encrypted

## Cost Optimization

- Use Render's free tier for development
- Scale down when not in use
- Use persistent disk for vector store
- Monitor API usage (OpenAI costs)

