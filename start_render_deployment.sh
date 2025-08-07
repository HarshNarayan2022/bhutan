#!/bin/bash
# Quick deployment script for Render Cloud
# Makes the deployment process even simpler

set -e

echo "🚀 Bhutan Mental Health Chatbot - Render Deployment"
echo "===================================================="

# Check if we're in the right directory
if [ ! -f "app_render.py" ]; then
    echo "❌ Error: app_render.py not found. Run this script from the project root."
    exit 1
fi

echo "📋 Step 1: Validating deployment files..."

# Check required files
required_files=("Dockerfile" "requirements_render.txt" "app_render.py" "render.yaml")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file found"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

echo ""
echo "🔧 Step 2: Running deployment preparation..."
python3 deploy_render.py

echo ""
echo "🐳 Step 3: Testing Docker build (optional)..."
read -p "Do you want to test Docker build locally? (y/N): " test_docker

if [[ $test_docker =~ ^[Yy]$ ]]; then
    echo "Building Docker image..."
    if command -v docker &> /dev/null; then
        python3 validate_docker.py
    else
        echo "⚠️ Docker not found. Skipping local test."
        echo "   You can still deploy to Render - they'll build the image."
    fi
fi

echo ""
echo "📊 Step 4: Deployment summary"
echo "============================"
echo "✅ Project ready for Render deployment"
echo ""
echo "🔗 Next steps:"
echo "1. Commit all files to your Git repository:"
echo "   git add ."
echo "   git commit -m 'Ready for Render deployment'"
echo "   git push origin main"
echo ""
echo "2. Go to https://render.com"
echo "3. Click 'New +' → 'Web Service'"
echo "4. Connect your repository"
echo "5. Configure:"
echo "   - Environment: Docker"
echo "   - Branch: main"
echo "   - Region: Choose closest to users"
echo ""
echo "6. Set environment variables:"
echo "   - PORT: 10000 (auto-set)"
echo "   - FLASK_ENV: production"
echo "   - SECRET_KEY: (generate secure key)"
echo ""
echo "7. Deploy and wait 5-10 minutes"
echo "8. Access at: https://your-app.onrender.com"
echo ""
echo "📱 Your mental health chatbot will be live!"
echo "🔍 Health check: https://your-app.onrender.com/health"
echo ""

# Create a quick Git status check
if command -v git &> /dev/null && [ -d ".git" ]; then
    echo "📋 Git status:"
    if git diff --quiet && git diff --staged --quiet; then
        echo "✅ No uncommitted changes"
    else
        echo "⚠️ You have uncommitted changes:"
        git status --short
        echo ""
        echo "💡 Commit your changes before deploying:"
        echo "   git add ."
        echo "   git commit -m 'Ready for Render deployment'"
        echo "   git push origin main"
    fi
else
    echo "⚠️ Not a Git repository. Initialize Git before deploying to Render."
fi

echo ""
echo "🎉 Deployment preparation complete!"
echo "Happy deploying! 🚀"
