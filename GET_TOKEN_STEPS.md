# How to Get Your GitHub Personal Access Token

## Step-by-Step Instructions

### Step 1: Go to GitHub Token Settings
**Direct Link**: https://github.com/settings/tokens

Or navigate manually:
1. Go to https://github.com
2. Click your profile picture (top right)
3. Click **"Settings"**
4. In the left sidebar, scroll down and click **"Developer settings"**
5. Click **"Personal access tokens"**
6. Click **"Tokens (classic)"**

### Step 2: Generate New Token
1. Click the green button: **"Generate new token"**
2. Select **"Generate new token (classic)"** (not fine-grained)

### Step 3: Configure Token
1. **Note** (name): `AI-Tuner-Agent-Setup` (or any name you want)
2. **Expiration**: Choose how long it should last (30 days, 90 days, or No expiration)
3. **Select scopes**: Check the box for **`repo`** (this gives full control of private repositories)
   - This will automatically check all repo-related permissions
4. Scroll down and click **"Generate token"** (green button at bottom)

### Step 4: Copy the Token
⚠️ **IMPORTANT**: GitHub will show you the token **ONCE**. Copy it immediately!

- The token will look like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- It's a long string starting with `ghp_`
- **Copy the entire token** - you won't be able to see it again!

### Step 5: Use the Token
Once you have the token, come back here and I'll help you push your code!

---

## Quick Link
**Direct link to create token**: https://github.com/settings/tokens/new

## What the Token Looks Like
```
ghp_1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
```

## Security Note
- The token acts as your password for Git operations
- Keep it secret - don't share it
- You can revoke it anytime at: https://github.com/settings/tokens
- After we push your code, I'll remove it from the git config for security

---

**Ready?** Once you have your token, let me know and I'll push your code! 🚀

