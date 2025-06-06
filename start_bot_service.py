#!/usr/bin/env python3
"""
Telegram Bot Background Service
Runs the bot continuously with proper error handling
"""

import os
import sys
import time
import logging
import threading
from pathlib import Path

# Setup path
sys.path.append(str(Path(__file__).parent))

from telegram_bot import QuickEscrowBot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_bot():
    """Run the bot with error recovery"""
    while True:
        try:
            logger.info("Starting QuickEscrowBot...")
            bot = QuickEscrowBot()
            logger.info("Bot initialized successfully - @QuickEscrowBot is online")
            bot.run()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Bot error: {e}")
            logger.info("Restarting bot in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()