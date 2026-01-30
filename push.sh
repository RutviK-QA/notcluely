#!/bin/bash
# Push changes to GitHub
echo "=== NotCluely - Preparing to deploy ==="
echo ""

# Check git is initialized
if [ ! -d .git ]; then
  echo "❌ Not a git repository. Initialize with: git init"
  exit 1
fi

# Add all changes
echo "📝 Staging changes..."
git add .

# Commit with message
echo "💾 Committing changes..."
git commit -m "Deploy: Switch to SQLite, add free deployment support, complete auth system"

# Push to main branch
echo "📤 Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Changes pushed to GitHub!"
echo ""
echo "NEXT STEPS:"
echo "1. Go to https://render.com and deploy the backend"
echo "2. Go to https://vercel.com and deploy the frontend"
echo "3. Update environment variables on each platform"
echo "4. See DEPLOYMENT_GUIDE.md for detailed steps"
echo ""
echo "Your app will be live in < 10 minutes! 🚀"
