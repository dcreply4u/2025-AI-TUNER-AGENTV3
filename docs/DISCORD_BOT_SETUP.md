# Discord Bot Setup Guide - AI Tuner Advisor Demo

## Overview

This guide will help you set up the AI Tuner Advisor Discord bot for pre-launch marketing and community building.

**Why This Is Great:**
- ✅ Showcases AI capabilities
- ✅ Builds community before launch
- ✅ Collects real user questions
- ✅ Low cost (free to host)
- ✅ Generates buzz and interest

---

## Prerequisites

1. **Discord Account** (free)
2. **Python 3.8+** installed
3. **Discord Bot Token** (we'll create this)
4. **Server to host bot** (can be free tier)

---

## Step 1: Create Discord Bot

### 1.1 Go to Discord Developer Portal
- Visit: https://discord.com/developers/applications
- Click "New Application"
- Name it "AI Tuner Advisor" (or your choice)
- Click "Create"

### 1.2 Create Bot
- Go to "Bot" section (left sidebar)
- Click "Add Bot"
- Click "Yes, do it!"
- **Copy the token** (you'll need this - keep it secret!)

### 1.3 Configure Bot
- **Username**: AI Tuner Advisor (or your choice)
- **Icon**: Upload your logo/icon
- **Description**: "AI-powered tuning advisor - Ask me anything about ECU tuning, fuel, timing, boost, and more!"
- **Public Bot**: OFF (for now, can enable later)
- **Requires OAuth2 Code Grant**: OFF
- **Message Content Intent**: ON (required for reading messages)

### 1.4 Invite Bot to Server
- Go to "OAuth2" > "URL Generator"
- Select scopes:
  - ✅ `bot`
  - ✅ `applications.commands` (optional, for slash commands)
- Select bot permissions:
  - ✅ `Send Messages`
  - ✅ `Read Message History`
  - ✅ `Embed Links`
  - ✅ `Use External Emojis`
- Copy the generated URL
- Open URL in browser
- Select your server
- Click "Authorize"

---

## Step 2: Install Dependencies

```bash
# Install discord.py
pip install discord.py

# Or add to requirements.txt
echo "discord.py>=2.3.0" >> requirements.txt
pip install -r requirements.txt
```

---

## Step 3: Configure Bot

### 3.1 Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:DISCORD_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
```

**Windows (Command Prompt):**
```cmd
set DISCORD_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
```

**Linux/Mac:**
```bash
export DISCORD_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
```

### 3.2 Or Create .env File

Create `.env` file in project root:
```
DISCORD_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
```

Then install python-dotenv:
```bash
pip install python-dotenv
```

And load in code:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Step 4: Run Bot

### 4.1 Test Locally

```bash
# From AI-TUNER-AGENT directory
python services/discord_bot.py YOUR_BOT_TOKEN
```

Or with environment variable:
```bash
python services/discord_bot.py
```

### 4.2 Verify It Works

1. Go to your Discord server
2. Type: `!tuner help`
3. Bot should respond with help message
4. Try: `!tuner ask How do I tune fuel?`
5. Bot should answer!

---

## Step 5: Deploy Bot (Choose One)

### Option 1: Free Hosting (Recommended for Demo)

#### Replit (Free Tier)
1. Go to https://replit.com
2. Create new Python repl
3. Upload `discord_bot.py`
4. Set `DISCORD_BOT_TOKEN` in Secrets
5. Click "Run"
6. Bot stays online (free tier has limits)

#### Railway (Free Tier)
1. Go to https://railway.app
2. New Project > Deploy from GitHub
3. Connect your repo
4. Set `DISCORD_BOT_TOKEN` in Variables
5. Deploy
6. Free tier: 500 hours/month

#### Render (Free Tier)
1. Go to https://render.com
2. New > Web Service
3. Connect GitHub repo
4. Build command: `pip install -r requirements.txt`
5. Start command: `python services/discord_bot.py`
6. Set `DISCORD_BOT_TOKEN` in Environment
7. Free tier: Spins down after inactivity

### Option 2: VPS (More Control)

#### DigitalOcean Droplet ($5/month)
1. Create Ubuntu droplet
2. SSH into server
3. Install Python and dependencies
4. Clone your repo
5. Set up systemd service (see below)
6. Bot runs 24/7

#### Systemd Service (Linux VPS)

Create `/etc/systemd/system/ai-tuner-bot.service`:
```ini
[Unit]
Description=AI Tuner Discord Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/AI-TUNER-AGENT
Environment="DISCORD_BOT_TOKEN=YOUR_TOKEN"
ExecStart=/usr/bin/python3 services/discord_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ai-tuner-bot
sudo systemctl start ai-tuner-bot
sudo systemctl status ai-tuner-bot
```

---

## Step 6: Customize Bot

### 6.1 Change Command Prefix

Edit `discord_bot.py`:
```python
bot = AITunerDiscordBot(
    token=token,
    command_prefix="!ai",  # Change this
    demo_mode=True,
)
```

### 6.2 Adjust Demo Limits

Edit demo stats in `discord_bot.py`:
```python
self.demo_stats = {
    'questions_answered': 0,
    'max_questions_per_user': 20,  # Change this
    'user_question_count': {},
}
```

### 6.3 Customize Welcome Message

Edit the help command response in `discord_bot.py`.

### 6.4 Add Custom Commands

Add new commands in `_setup_commands()` method:
```python
@self.bot.command(name='feature')
async def feature_command(ctx: commands.Context):
    await ctx.send("Check out our website: https://your-site.com")
```

---

## Step 7: Promote Bot

### 7.1 Server Setup
- Create dedicated channel: `#ai-tuner-advisor`
- Pin welcome message
- Add bot description in channel topic
- Set up role permissions

### 7.2 Marketing
- Announce in your community
- Share on social media
- Add to Discord server list
- Create demo video
- Blog post about the bot

### 7.3 Community Engagement
- Monitor questions
- Collect feedback
- Improve responses
- Add requested features
- Build anticipation for launch

---

## Commands Reference

### User Commands:
- `!tuner ask <question>` - Ask the AI advisor
- `!tuner help` - Show help
- `!tuner stats` - Show demo statistics
- `!tuner examples` - Show example questions

### Mention Bot:
- `@AI Tuner Advisor How do I tune fuel?` - Bot responds to mentions

---

## Demo Mode Features

### Limitations:
- ✅ 10 questions per user (configurable)
- ✅ Shows "Full version coming soon" message
- ✅ Tracks usage statistics
- ✅ No live telemetry (demo only)

### Benefits:
- ✅ Generates interest
- ✅ Showcases capabilities
- ✅ Collects feedback
- ✅ Builds community

---

## Troubleshooting

### Bot Not Responding:
- ✅ Check bot is online (green dot in Discord)
- ✅ Check bot has permissions
- ✅ Check command prefix is correct
- ✅ Check bot token is valid
- ✅ Check logs for errors

### Import Errors:
```bash
pip install discord.py
pip install python-dotenv  # If using .env
```

### Token Issues:
- ✅ Token must be kept secret
- ✅ Regenerate if exposed
- ✅ Use environment variables (not hardcoded)

### Hosting Issues:
- ✅ Check server logs
- ✅ Verify Python version (3.8+)
- ✅ Check dependencies installed
- ✅ Verify environment variables set

---

## Security Best Practices

1. **Never commit token to Git**
   - Add to `.gitignore`
   - Use environment variables
   - Use secrets management

2. **Rotate token if exposed**
   - Go to Discord Developer Portal
   - Regenerate token
   - Update environment variable

3. **Limit bot permissions**
   - Only grant necessary permissions
   - Don't give admin access
   - Review permissions regularly

4. **Monitor usage**
   - Watch for abuse
   - Rate limit if needed
   - Block problematic users

---

## Next Steps

1. ✅ Deploy bot to server
2. ✅ Test all commands
3. ✅ Customize for your brand
4. ✅ Promote in communities
5. ✅ Collect feedback
6. ✅ Improve responses
7. ✅ Build anticipation for launch

---

## Support

If you need help:
- Check Discord.py docs: https://discordpy.readthedocs.io/
- Check bot logs for errors
- Review this guide
- Test commands locally first

---

## Cost Estimate

**Free Option:**
- Replit/Railway/Render free tier
- **Cost: $0/month**
- Limitations: May spin down, limited resources

**Paid Option:**
- DigitalOcean Droplet ($5/month)
- **Cost: $5/month**
- Benefits: Always online, full control

**Recommended for Demo:**
- Start with free tier
- Upgrade if needed
- **Total: $0-5/month**

---

## Success Metrics

Track these to measure success:
- Questions answered per day
- Unique users
- Most common questions
- User feedback
- Community growth
- Interest in full product

---

**Good luck with your pre-launch marketing! 🚀**










