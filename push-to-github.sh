#!/bin/bash
# Push rffl-tools to GitHub

set -e

echo "🚀 Pushing rffl-tools to GitHub..."
echo ""

# Check if remote already exists
if git remote get-url origin >/dev/null 2>&1; then
    echo "✅ Remote 'origin' already configured"
    git remote -v
else
    echo "📝 Adding remote 'origin'..."
    git remote add origin https://github.com/thorsenk/rffl-tools.git
    echo "✅ Remote added"
fi

echo ""
echo "📤 Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ Successfully pushed to GitHub!"
echo "🌐 Repository: https://github.com/thorsenk/rffl-tools"

