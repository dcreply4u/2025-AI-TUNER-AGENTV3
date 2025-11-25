"""
Quick Start Script for Discord Bot

Simple launcher for the AI Tuner Advisor Discord bot.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables if .env exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Get token from command line or environment
token = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DISCORD_BOT_TOKEN")

if not token:
    print("=" * 60)
    print("AI Tuner Advisor - Discord Bot")
    print("=" * 60)
    print()
    print("Usage:")
    print("  python start_discord_bot.py <DISCORD_BOT_TOKEN>")
    print()
    print("Or set environment variable:")
    print("  set DISCORD_BOT_TOKEN=your_token_here")
    print("  python start_discord_bot.py")
    print()
    print("Or create .env file:")
    print("  DISCORD_BOT_TOKEN=your_token_here")
    print()
    print("Get your bot token from:")
    print("  https://discord.com/developers/applications")
    print("=" * 60)
    sys.exit(1)

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import and run bot
try:
    from services.discord_bot import create_demo_bot
    
    print("=" * 60)
    print("Starting AI Tuner Advisor Discord Bot...")
    print("=" * 60)
    print()
    print("Bot Features:")
    print("  • AI-powered tuning advice")
    print("  • Expert knowledge base")
    print("  • Demo mode (10 questions per user)")
    print("  • Pre-launch marketing tool")
    print()
    print("Commands:")
    print("  !tuner ask <question>  - Ask the AI advisor")
    print("  !tuner help            - Show help")
    print("  !tuner stats           - Show demo stats")
    print("  !tuner examples        - Show examples")
    print()
    print("Press Ctrl+C to stop the bot")
    print("=" * 60)
    print()
    
    bot = create_demo_bot(token)
    bot.run()
    
except KeyboardInterrupt:
    print("\n\nBot stopped by user")
except Exception as e:
    print(f"\n\nError: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)










