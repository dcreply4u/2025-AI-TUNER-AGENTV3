# How to Push to GitHub

## Step 1: Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `ai-tuner-agent` (or your preferred name)
3. Description: "AI-powered racing telemetry and tuning system"
4. Choose Public or Private
5. **DO NOT** check "Initialize with README"
6. Click "Create repository"

## Step 2: Connect and Push

After creating the repo, GitHub will show you commands. Use these:

```bash
# Add your GitHub repository as remote (replace YOUR_USERNAME and REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Or if using SSH (if you have SSH keys set up):
# git remote add origin git@github.com:YOUR_USERNAME/REPO_NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Alternative: Using GitHub CLI (if installed)

If you have GitHub CLI installed:

```bash
gh repo create ai-tuner-agent --public --source=. --remote=origin --push
```

## Authentication

If you're prompted for credentials:
- **Username**: Your GitHub username
- **Password**: Use a Personal Access Token (not your password)
  - Create one at: https://github.com/settings/tokens
  - Select scope: `repo` (full control of private repositories)

## Troubleshooting

If you get authentication errors:
1. Use GitHub CLI: `gh auth login`
2. Or use SSH keys instead of HTTPS
3. Or use a Personal Access Token as password

