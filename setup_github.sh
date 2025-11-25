#!/bin/bash
# Bash script to set up GitHub repository
# Run this after creating the repository on GitHub

GITHUB_USERNAME="${1:-}"
REPO_NAME="${2:-ai-tuner-agent}"

if [ -z "$GITHUB_USERNAME" ]; then
    echo "Usage: ./setup_github.sh <github-username> [repo-name]"
    echo "Example: ./setup_github.sh dcreply4u ai-tuner-agent"
    exit 1
fi

echo "Setting up GitHub repository..."

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "Error: Not in a git repository. Run 'git init' first."
    exit 1
fi

# Check if remote already exists
if git remote get-url origin &>/dev/null; then
    echo "Remote 'origin' already exists: $(git remote get-url origin)"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    git remote remove origin
fi

# Add remote
REMOTE_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
echo "Adding remote: $REMOTE_URL"
git remote add origin "$REMOTE_URL"

# Rename branch to main if needed
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Renaming branch from '$CURRENT_BRANCH' to 'main'..."
    git branch -M main
fi

# Check if there are uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Uncommitted changes detected. Staging and committing..."
    git add .
    git commit -m "Update: Prepare for GitHub push"
fi

# Push to GitHub
echo "Pushing to GitHub..."
echo "Note: You may be prompted for credentials."
echo "Use a Personal Access Token as password: https://github.com/settings/tokens"
echo ""

git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "Success! Repository pushed to GitHub."
    echo "View at: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
else
    echo ""
    echo "Push failed. Common issues:"
    echo "1. Repository doesn't exist on GitHub - create it first at https://github.com/new"
    echo "2. Authentication failed - use Personal Access Token instead of password"
    echo "3. Network issues - check your internet connection"
fi

