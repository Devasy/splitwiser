# Railway Deployment Guide

This project is configured for deployment on Railway using multiple approaches:

## Deployment Options

### Option 1: Nixpacks (Recommended)
Railway will automatically detect the `nixpacks.toml` file and use Nixpacks for building.

### Option 2: Dockerfile
Railway will use the Dockerfile if Nixpacks is not preferred.

### Option 3: Procfile
Fallback option using the Procfile.

## Configuration Files

- `railway.toml` - Railway-specific configuration
- `nixpacks.toml` - Nixpacks build configuration  
- `Dockerfile` - Docker build configuration
- `Procfile` - Process configuration
- `.dockerignore` - Files to exclude from Docker build

## Environment Variables to Set in Railway

**Important**: Do NOT upload your `.env` file to GitHub or Railway. Instead, set environment variables through Railway's dashboard.

### How to Set Environment Variables in Railway:
1. Go to your Railway project dashboard
2. Click on the "Variables" tab
3. Add each variable individually using the format: `VARIABLE_NAME=value`

### Required Variables
```
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/database
SECRET_KEY=your-super-secure-jwt-secret-key-generate-a-new-one
ALLOWED_ORIGINS=https://your-frontend-domain.com,https://your-app.vercel.app,http://localhost:3000
FRONTEND_URL=https://your-frontend-domain.netlify.app
```

**Important for Splitwise OAuth**: The `FRONTEND_URL` variable is critical for the Splitwise import functionality. It must be set to your production frontend URL (e.g., `https://your-app.netlify.app` or `https://your-app.vercel.app`). Without this, the OAuth callback will fail in production.

### Optional Variables (with defaults)
```
DATABASE_NAME=splitwiser
DEBUG=false
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
ALGORITHM=HS256
```

### Firebase Service Account Credentials
Instead of uploading the Firebase service account JSON file, you need to set the following environment variables from your service account JSON:

```
FIREBASE_TYPE=service_account
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account-email@project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your-service-account
```

To easily convert your Firebase service account JSON to environment variables, run:
```
python backend/convert_service_account_to_env.py backend/firebase-service-account.json
```

**Important Note:** The `FIREBASE_PRIVATE_KEY` must include all newlines. Railway's environment variables support multiline values, but be careful with the formatting.

## Debugging CORS Issues

If you're experiencing CORS issues (OPTIONS requests failing with 400 errors), follow these steps:

1. **Verify ALLOWED_ORIGINS Environment Variable**:
   Make sure your Railway deployment has the correct `ALLOWED_ORIGINS` set with your frontend domain:
   ```
   ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app,http://localhost:3000
   ```

2. **Test CORS Configuration**:
   Use the provided test script:
   ```bash
   cd backend
   pip install requests
   # Edit test_cors.py to use your backend and frontend URLs
   python test_cors.py
   ```

3. **Check Railway Logs**:
   Look for CORS-related messages in your Railway deployment logs. The enhanced logging will show:
   - Allowed CORS origins on startup
   - OPTIONS request details
   - Origin headers from requests

4. **Common CORS Issues**:
   - Frontend domain not included in ALLOWED_ORIGINS
   - Trailing slashes in URLs (e.g., `https://domain.com/` vs `https://domain.com`)
   - HTTP vs HTTPS mismatch
   - Wrong port numbers in localhost URLs

### Example of Setting Variables in Railway:
- Variable: `MONGODB_URL`
- Value: `mongodb+srv://myuser:mypassword@cluster0.abc123.mongodb.net/splitwiser`

The app will automatically use these environment variables instead of the `.env` file.

## Deployment Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add Railway deployment configuration"
   git push origin main
   ```

2. **Connect to Railway**
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Environment Variables**
   - In Railway dashboard, go to Variables tab
   - Add all required environment variables listed above

4. **Deploy**
   - Railway will automatically build and deploy
   - Monitor the build logs for any issues

## Build Process

The build process will:
1. Install Python 3.12
2. Install dependencies from `requirements.txt`
3. Start the FastAPI server with uvicorn

## Health Check

Your deployed API will be available at:
- Main API: `https://your-app.railway.app/`
- Health check: `https://your-app.railway.app/health`
- API docs: `https://your-app.railway.app/docs`

## Performance Optimizations

The Splitwise import functionality has been optimized for serverless and free-tier deployments:

### Concurrent Processing
- **Async API Calls**: All Splitwise API calls use `asyncio.to_thread()` to prevent blocking
- **Parallel Expense Processing**: Expenses are processed in parallel using `asyncio.gather()` with a semaphore (limit: 10 concurrent operations)
- **Batch Preview Generation**: Group expense counts are fetched concurrently during preview

### Benefits
- **5-10x faster imports** on free-tier Railway deployments
- **Reduced memory usage** through controlled concurrency
- **Better serverless behavior** with non-blocking I/O operations

### Configuration
The default concurrency limit is set to 10 for Railway free tier. If you're on a paid plan with more resources, you can adjust the semaphore limits in:
- `backend/app/integrations/service.py` - `_import_expenses()` method
- Preview endpoint concurrency in `preview_splitwise_import()` method

## Troubleshooting

### Common Issues:
1. **Build fails**: Check that all dependencies in `requirements.txt` are valid
2. **App won't start**: Verify environment variables are set correctly
3. **CORS errors**: Make sure `ALLOWED_ORIGINS` includes your frontend domain
4. **Database connection**: Verify `MONGODB_URL` is correct and accessible
5. **Splitwise OAuth fails**: Ensure `FRONTEND_URL` is set to your production frontend URL and matches the callback URL registered in your Splitwise app settings

### Logs:
Check Railway deployment logs in the dashboard for detailed error messages.
