# Render.com Deployment Guide

This guide covers deploying the Mental Health Chatbot application to Render.com using Docker.

## 🚀 Quick Deployment

### 1. Prerequisites
- GitHub repository with this codebase
- Render.com account (free tier available)
- API keys from Google, Groq, and OpenAI

### 2. Deploy to Render

#### Step 1: Create Web Service
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Choose "Docker" as the runtime

#### Step 2: Configure Service
- **Name**: `mental-health-chatbot`
- **Region**: Choose closest to your users
- **Branch**: `main`
- **Root Directory**: Leave empty
- **Dockerfile Path**: `./Dockerfile`

#### Step 3: Set Environment Variables
Add these in the "Environment" section:

```env
# Required API Keys
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key  
OPENAI_API_KEY=your_openai_api_key

# Security
SECRET_KEY=your_super_secure_secret_key
FLASK_SECRET_KEY=your_flask_secret_key

# Production Settings
FLASK_ENV=production
DEBUG=false
SESSION_COOKIE_SECURE=true

# CORS (replace with your actual domain)
ALLOWED_ORIGINS=https://your-app-name.onrender.com
```

#### Step 4: Deploy
1. Click "Create Web Service"
2. Wait for build and deployment (5-10 minutes)
3. Access your app at the provided URL

## 🔧 Configuration Details

### Port Configuration
- Render automatically provides `PORT` environment variable
- Application is configured to use `$PORT` (default: 10000)
- No manual port configuration needed

### Health Checks
- Flask health endpoint: `https://your-app.onrender.com/health`
- FastAPI health endpoint: `https://your-app.onrender.com/fastapi-health` (internal)
- Automatic health monitoring included
- Process restart mechanism for crashed services

### Service Architecture
- **Single Container**: Flask + FastAPI in one container
- **Background Process**: FastAPI runs on internal port
- **Main Process**: Flask serves web interface on `$PORT`

## 📊 Monitoring

### Logs
Access logs in Render dashboard:
- Build logs during deployment
- Runtime logs for debugging
- Error tracking and monitoring

### Metrics
Monitor in Render dashboard:
- CPU and memory usage
- Request volume and response times
- Service uptime and health

## 🛠️ Troubleshooting

### Common Issues

#### Build Failures
```bash
# Check build logs for:
- Missing environment variables
- Dependency installation errors
- Docker build issues
```

#### Runtime Errors
```bash
# Check service logs for:
- API key validation
- Service startup issues
- Database connection problems
- FastAPI backend crashes
- Email validator dependency issues
```

#### FastAPI Backend Issues
```bash
# Common FastAPI problems:
- Missing email-validator: Fixed in requirements
- Process crashes: Auto-restart mechanism enabled
- Memory issues: Optimized memory settings applied
- SQLAlchemy text() errors: Fixed in health checks
```

#### Health Check Failures
```bash
# Verify:
- Health endpoint responds: /health
- All services started properly
- No critical startup errors
```

### Performance Tips
- **Memory**: Free tier provides 512MB (sufficient for basic usage)
- **CPU**: Shared CPU on free tier (upgrade for better performance)
- **Scaling**: Render auto-scales based on traffic

## 🔄 Updates and Maintenance

### Automatic Deploys
- Enable auto-deploy from GitHub
- Pushes to main branch trigger deployment
- Monitor deployment status in dashboard

### Manual Deploys
- Use "Manual Deploy" button in dashboard
- Deploy specific commits or branches
- Rollback to previous deployments if needed

### Environment Updates
- Update environment variables in dashboard
- Restart service after changes
- Test thoroughly after updates

## 💰 Cost Estimation

### Free Tier
- **Limitations**: 512MB RAM, shared CPU, 750 hours/month
- **Cost**: $0/month
- **Suitable for**: Development, testing, light usage

### Paid Plans
- **Starter**: $7/month, dedicated resources
- **Standard**: $25/month, enhanced performance
- **Pro**: $85/month, priority support

## 🔗 Useful Links

- [Render Documentation](https://render.com/docs)
- [Docker on Render](https://render.com/docs/docker)
- [Environment Variables](https://render.com/docs/environment-variables)
- [Health Checks](https://render.com/docs/health-checks)

## 📞 Support

For deployment issues:
1. Check Render service logs
2. Review this deployment guide
3. Consult Render documentation
4. Create GitHub issue for app-specific problems
