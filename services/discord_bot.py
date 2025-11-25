"""
Discord Bot Integration for AI Tuner Advisor

Demo version of the AI advisor that can answer questions in Discord.
Perfect for pre-launch marketing and community building.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

LOGGER = logging.getLogger(__name__)

# Discord.py is optional - install with: pip install discord.py
try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    discord = None  # type: ignore
    commands = None  # type: ignore

# Import enhanced advisor
try:
    from services.ai_advisor_q_enhanced import EnhancedAIAdvisorQ, ResponseResult
    ADVISOR_AVAILABLE = True
except ImportError:
    try:
        from services.ai_advisor_q import AIAdvisorQ
        EnhancedAIAdvisorQ = AIAdvisorQ
        ADVISOR_AVAILABLE = True
    except ImportError:
        ADVISOR_AVAILABLE = False
        EnhancedAIAdvisorQ = None  # type: ignore


class AITunerDiscordBot:
    """
    Discord bot for AI Tuner Advisor demo.
    
    Features:
    - Answers tuning questions
    - Provides expert advice
    - Demo mode limitations
    - Pre-launch marketing tool
    """
    
    def __init__(
        self,
        token: str,
        command_prefix: str = "!tuner",
        demo_mode: bool = True,
    ) -> None:
        """
        Initialize Discord bot.
        
        Args:
            token: Discord bot token
            command_prefix: Command prefix (default: !tuner)
            demo_mode: Enable demo mode limitations
        """
        if not DISCORD_AVAILABLE:
            raise ImportError("discord.py not installed. Install with: pip install discord.py")
        
        if not ADVISOR_AVAILABLE:
            raise ImportError("AI Advisor not available")
        
        self.token = token
        self.demo_mode = demo_mode
        self.command_prefix = command_prefix
        
        # Initialize bot
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(
            command_prefix=command_prefix,
            intents=intents,
            help_command=None,  # Custom help
        )
        
        # Initialize advisor
        self.advisor = EnhancedAIAdvisorQ(
            use_llm=False,  # Can enable if you have API key
            config_monitor=None,
            telemetry_provider=None,  # No live telemetry in Discord
        )
        
        # Demo mode stats
        self.demo_stats = {
            'questions_answered': 0,
            'max_questions_per_user': 10,  # Demo limitation
            'user_question_count': {},
        }
        
        # Setup commands
        self._setup_commands()
        
        # Setup events
        self._setup_events()
    
    def _setup_commands(self) -> None:
        """Setup bot commands."""
        
        @self.bot.command(name='ask', aliases=['q', 'question'])
        async def ask_command(ctx: commands.Context, *, question: str) -> None:
            """Ask the AI Tuner advisor a question."""
            # Check demo mode limits
            if self.demo_mode:
                user_id = str(ctx.author.id)
                count = self.demo_stats['user_question_count'].get(user_id, 0)
                
                if count >= self.demo_stats['max_questions_per_user']:
                    await ctx.send(
                        f"⚠️ **Demo Mode Limit Reached**\n\n"
                        f"You've used {count} questions in demo mode. "
                        f"To unlock unlimited questions, check out the full AI Tuner Agent!\n\n"
                        f"🔗 **Coming Soon** - Full version with unlimited AI assistance, "
                        f"real-time telemetry analysis, and advanced tuning features."
                    )
                    return
                
                self.demo_stats['user_question_count'][user_id] = count + 1
                self.demo_stats['questions_answered'] += 1
                remaining = self.demo_stats['max_questions_per_user'] - count - 1
            
            # Get response from advisor
            try:
                result = self.advisor.ask(question)
                
                # Handle both ResponseResult and string
                if hasattr(result, 'answer'):
                    answer = result.answer
                    confidence = result.confidence
                    sources = result.sources
                else:
                    answer = result
                    confidence = 1.0
                    sources = []
                
                # Format response
                response = f"**Q's Answer:**\n\n{answer}"
                
                # Add demo mode info
                if self.demo_mode:
                    response += f"\n\n---\n"
                    response += f"📊 **Demo Mode** - {remaining} questions remaining\n"
                    response += f"🚀 **Full Version Coming Soon** - Unlimited AI assistance + real-time telemetry"
                
                # Add confidence if low
                if confidence < 0.7:
                    response += f"\n\n⚠️ *Confidence: {confidence:.0%}*"
                
                # Add sources if available
                if sources:
                    response += f"\n\n📚 *Sources: {', '.join(sources[:3])}*"
                
                # Send response (split if too long)
                if len(response) > 2000:
                    # Discord has 2000 char limit
                    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                    for chunk in chunks:
                        await ctx.send(chunk)
                else:
                    await ctx.send(response)
                    
            except Exception as e:
                LOGGER.error(f"Error answering question: {e}")
                await ctx.send(
                    f"❌ Sorry, I encountered an error: {str(e)}\n\n"
                    f"Try rephrasing your question or ask about:\n"
                    f"• Fuel tuning\n• Ignition timing\n• Boost control\n• ECU configuration"
                )
        
        @self.bot.command(name='help', aliases=['h'])
        async def help_command(ctx: commands.Context) -> None:
            """Show help information."""
            help_text = f"""
**🤖 AI Tuner Advisor - Demo Bot**

**Commands:**
`{self.command_prefix}ask <question>` - Ask the AI advisor a question
`{self.command_prefix}help` - Show this help message
`{self.command_prefix}stats` - Show demo statistics
`{self.command_prefix}examples` - Show example questions

**What I Can Help With:**
• Fuel tuning and AFR targets
• Ignition timing optimization
• Boost control setup
• Nitrous/methanol/E85 tuning
• Launch control and anti-lag
• ECU configuration
• Troubleshooting issues
• Software features

**Demo Mode:**
• Limited to {self.demo_stats['max_questions_per_user']} questions per user
• Full version coming soon with unlimited access!

**Example Questions:**
• "How do I tune fuel?"
• "What is the optimal AFR?"
• "How do I set up launch control?"
• "What boost pressure should I run?"

🚀 **Full AI Tuner Agent Coming Soon!**
            """
            await ctx.send(help_text)
        
        @self.bot.command(name='stats')
        async def stats_command(ctx: commands.Context) -> None:
            """Show demo statistics."""
            if not self.demo_mode:
                await ctx.send("Stats are only available in demo mode.")
                return
            
            user_id = str(ctx.author.id)
            user_count = self.demo_stats['user_question_count'].get(user_id, 0)
            remaining = self.demo_stats['max_questions_per_user'] - user_count
            
            stats_text = f"""
**📊 Demo Statistics**

**Your Usage:**
• Questions asked: {user_count}/{self.demo_stats['max_questions_per_user']}
• Questions remaining: {remaining}

**Total Demo Usage:**
• Total questions answered: {self.demo_stats['questions_answered']}

🚀 **Unlock unlimited questions with the full AI Tuner Agent!**
            """
            await ctx.send(stats_text)
        
        @self.bot.command(name='examples', aliases=['ex'])
        async def examples_command(ctx: commands.Context) -> None:
            """Show example questions."""
            examples = """
**💡 Example Questions:**

**Tuning Questions:**
• "How do I tune fuel for maximum power?"
• "What is the optimal ignition timing?"
• "How do I set up boost control?"
• "What AFR should I target at WOT?"

**Feature Questions:**
• "How do I configure launch control?"
• "How do I set up anti-lag?"
• "How do I tune nitrous?"
• "How do I use methanol injection?"

**Troubleshooting:**
• "My engine is running too rich"
• "I'm getting knock, what should I do?"
• "How do I fix boost spikes?"

**General:**
• "What are the best practices for tuning?"
• "How do I use Local Autotune?"
• "What keyboard shortcuts are available?"

Ask me anything about tuning, ECU configuration, or the AI Tuner software!
            """
            await ctx.send(examples)
    
    def _setup_events(self) -> None:
        """Setup bot events."""
        
        @self.bot.event
        async def on_ready() -> None:
            """Called when bot is ready."""
            LOGGER.info(f'{self.bot.user} has connected to Discord!')
            LOGGER.info(f'Bot is in {len(self.bot.guilds)} guilds')
            
            # Set status
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{self.command_prefix}help for help"
            )
            await self.bot.change_presence(activity=activity)
        
        @self.bot.event
        async def on_message(message: discord.Message) -> None:
            """Handle messages."""
            # Ignore bot messages
            if message.author.bot:
                return
            
            # Check if bot is mentioned
            if self.bot.user and self.bot.user.mentioned_in(message):
                # Extract question (remove mention)
                content = message.content
                for mention in message.mentions:
                    content = content.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '')
                content = content.strip()
                
                if content:
                    # Answer question
                    ctx = await self.bot.get_context(message)
                    await ask_command(ctx, question=content)
                else:
                    await message.channel.send(
                        f"Hi! I'm the AI Tuner Advisor. Ask me anything about tuning!\n"
                        f"Use `{self.command_prefix}help` for commands."
                    )
            
            # Process commands
            await self.bot.process_commands(message)
        
        @self.bot.event
        async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
            """Handle command errors."""
            if isinstance(error, commands.CommandNotFound):
                return  # Ignore unknown commands
            
            LOGGER.error(f"Command error: {error}")
            await ctx.send(
                f"❌ Error: {str(error)}\n\n"
                f"Use `{self.command_prefix}help` for available commands."
            )
    
    async def start(self) -> None:
        """Start the bot."""
        if not self.token:
            raise ValueError("Discord bot token is required")
        
        LOGGER.info("Starting Discord bot...")
        await self.bot.start(self.token)
    
    def run(self) -> None:
        """Run the bot (blocking)."""
        if not self.token:
            raise ValueError("Discord bot token is required")
        
        LOGGER.info("Starting Discord bot...")
        self.bot.run(self.token)


def create_demo_bot(token: Optional[str] = None) -> AITunerDiscordBot:
    """
    Create a demo Discord bot instance.
    
    Args:
        token: Discord bot token (or from DISCORD_BOT_TOKEN env var)
        
    Returns:
        Configured Discord bot
    """
    if not token:
        token = os.environ.get("DISCORD_BOT_TOKEN")
    
    if not token:
        raise ValueError(
            "Discord bot token required. "
            "Set DISCORD_BOT_TOKEN environment variable or pass token parameter."
        )
    
    return AITunerDiscordBot(
        token=token,
        command_prefix="!tuner",
        demo_mode=True,
    )


if __name__ == "__main__":
    # Example usage
    import sys
    
    # Get token from command line or environment
    token = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DISCORD_BOT_TOKEN")
    
    if not token:
        print("Usage: python discord_bot.py <DISCORD_BOT_TOKEN>")
        print("Or set DISCORD_BOT_TOKEN environment variable")
        sys.exit(1)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run bot
    bot = create_demo_bot(token)
    bot.run()










