# Vercel Deployment Guide

This guide explains how to deploy the frontend to Vercel.

## Prerequisites

- A Vercel account (free tier works)
- Backend API deployed and accessible
- Environment variables configured

## Deployment Steps

### 1. Push to Git Repository

Make sure your code is pushed to a Git repository (GitHub, GitLab, or Bitbucket).

```bash
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main
```

### 2. Deploy to Vercel

#### Option A: Via Vercel Dashboard

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your Git repository
4. Configure the project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`

#### Option B: Via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy
cd frontend
vercel

# Follow the prompts
```

### 3. Configure Environment Variables

In your Vercel project settings, add the following environment variable:

- **NEXT_PUBLIC_API_URL**: Your backend API URL
  - Example: `https://your-backend-domain.com/api/v1`
  - For local testing: `http://localhost:8000/api/v1`

#### To Add Environment Variables:

1. Go to your project in Vercel dashboard
2. Navigate to **Settings** → **Environment Variables**
3. Add `NEXT_PUBLIC_API_URL` with your backend URL
4. Select environments (Production, Preview, Development)
5. Click **Save**
6. Redeploy the application

### 4. Build Configuration

The project is already configured with:
- `next.config.ts` - Next.js configuration
- `vercel.json` - Vercel-specific settings
- `.env.example` - Environment variable template

## Troubleshooting

### Build Fails

**Error: Module not found**
- Make sure all dependencies are in `package.json`
- Run `npm install` locally to verify

**Error: TypeScript errors**
- Check `tsconfig.json` configuration
- Fix any TypeScript errors before deploying

**Error: ESLint errors**
- The build will fail if there are critical ESLint errors
- Fix errors or temporarily disable in `next.config.ts`

### Runtime Errors

**API calls fail (CORS)**
- Ensure your backend has CORS configured to allow your Vercel domain
- Check `NEXT_PUBLIC_API_URL` is set correctly

**Environment variables not working**
- Make sure variables start with `NEXT_PUBLIC_` for client-side access
- Redeploy after adding environment variables

**404 errors on routes**
- Verify Next.js routing is configured correctly
- Check `app/` directory structure

### Performance Issues

**Slow initial load**
- Enable Next.js Image Optimization
- Use Vercel's Edge Network (automatic)
- Consider enabling ISR (Incremental Static Regeneration) for static pages

## Environment Variables

### Required

- `NEXT_PUBLIC_API_URL` - Backend API URL

### Optional

- `NEXT_PUBLIC_APP_NAME` - Application name (defaults to "MediClaim AI")
- `NEXT_PUBLIC_APP_VERSION` - Application version

## Build Settings

The project uses these build settings:

- **Framework**: Next.js 16
- **Node Version**: 18.x (Vercel default)
- **Build Command**: `npm run build`
- **Output Directory**: `.next`

## Post-Deployment

After deployment:

1. **Test the application**: Visit your Vercel URL
2. **Check API connectivity**: Ensure backend is accessible
3. **Monitor logs**: Check Vercel dashboard for errors
4. **Set up custom domain** (optional): Configure in Vercel settings

## Continuous Deployment

Vercel automatically deploys on every push to your main branch:

- **Production**: Deploys from `main` branch
- **Preview**: Deploys from feature branches and PRs
- **Development**: Deploys from `dev` branch (if configured)

## Support

For issues:
- Check Vercel deployment logs
- Review Next.js build output
- Verify environment variables are set
- Ensure backend API is accessible

