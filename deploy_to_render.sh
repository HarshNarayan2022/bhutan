#!/bin/bash
# Deploy to Render - Commit and Push Script

echo "🚀 Preparing for Render Deployment"
echo "=================================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not a git repository. Initialize git first:"
    echo "   git init"
    echo "   git remote add origin <your-repo-url>"
    exit 1
fi

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --staged --quiet; then
    echo "📝 Found uncommitted changes:"
    git status --short
    echo ""
    
    # Add all changes
    echo "📦 Adding all changes..."
    git add .
    
    # Commit changes
    echo "💾 Committing changes..."
    git commit -m "🚀 Production deployment setup for Render

- Flask frontend (main.py) + FastAPI backend (fastapi_app.py)
- Memory optimized for 512MB RAM
- Multi-service architecture with supervisor
- HTTP proxy for traffic routing
- Production-ready Docker configuration

Ready for Render cloud deployment!"
    
    echo "✅ Changes committed successfully!"
else
    echo "✅ No uncommitted changes found"
fi

# Push to remote
echo "🌐 Pushing to remote repository..."
if git push origin main 2>/dev/null || git push origin master 2>/dev/null; then
    echo "✅ Successfully pushed to remote!"
else
    echo "❌ Failed to push. Check your remote repository settings."
    echo "💡 Make sure you have:"
    echo "   - Added a remote: git remote add origin <your-repo-url>"
    echo "   - Set up authentication (SSH key or token)"
    exit 1
fi

echo ""
echo "🎉 Repository is ready for Render deployment!"
echo ""
echo "🔗 Next steps:"
echo "1. Go to https://render.com"
echo "2. Create new Web Service"
echo "3. Connect your repository"
echo "4. Set Environment: Docker"
echo "5. Add environment variables:"
echo "   - FLASK_ENV=production"
echo "   - SECRET_KEY=<generate-secure-key>"
echo "   - GROQ_API_KEY=<your-key> (optional)"
echo "   - GOOGLE_API_KEY=<your-key> (optional)"
echo ""
echo "🚀 Deploy and wait 5-10 minutes!"
echo "✅ Your app will be live at: https://your-app.onrender.com"
