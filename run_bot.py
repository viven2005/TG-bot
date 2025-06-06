#!/usr/bin/env python3
"""
QuickEscrowBot Runner
Starts the Telegram bot with proper environment setup
"""

import os
import sys
from dotenv import load_dotenv
from telegram_bot import QuickEscrowBot

# Load environment variables
load_dotenv()

def main():
    """Main function to run the bot"""
    try:
        print("🛡️ Starting QuickEscrowBot...")
        
        # Initialize and run the bot
        bot = QuickEscrowBot()
        print("✅ Bot initialized successfully!")
        print("🚀 Bot is now running and ready to receive messages...")
        
        # Start polling
        bot.run()
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Please check your environment variables.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()