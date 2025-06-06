#!/usr/bin/env python3
"""
QuickEscrowBot - Advanced Telegram Escrow Bot
Secure transaction management with animated UI integration
"""

import os
import asyncio
import logging
import json
import qrcode
import io
import base64
from datetime import datetime
from typing import Dict, Optional

import telebot
from telebot import types
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuickEscrowBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.api_base_url = os.getenv('API_BASE_URL', 'http://0.0.0.0:5000/api')
        self.upi_id = "quickescrow@upi"
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        self.bot = telebot.TeleBot(self.bot_token)
        self.user_sessions: Dict[int, Dict] = {}
        
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all bot command and message handlers"""
        
        @self.bot.message_handler(commands=['start'])
        def start_command(message):
            self.handle_start(message)
        
        @self.bot.message_handler(commands=['escrow'])
        def escrow_command(message):
            self.handle_escrow_start(message)
        
        @self.bot.message_handler(commands=['status'])
        def status_command(message):
            self.handle_status_check(message)
        
        @self.bot.message_handler(commands=['help'])
        def help_command(message):
            self.handle_help(message)
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call):
            self.handle_callback(call)
        
        @self.bot.message_handler(func=lambda message: True)
        def message_handler(message):
            self.handle_message(message)
    
    def handle_start(self, message):
        """Handle /start command with animated welcome"""
        user_id = message.from_user.id
        username = message.from_user.username or "User"
        
        # Initialize user session
        self.user_sessions[user_id] = {
            'state': 'welcome',
            'username': username
        }
        
        # Send animated welcome message
        welcome_text = """
🛡️ **Welcome to QuickEscrowBot!** ⚡

🔹 *Secure* • *Fast* • *Reliable* Escrow Service

Let's get started on your secure transaction journey! 💸

Choose an option below to begin:
        """
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("🚀 Start Escrow", callback_data="start_escrow"),
            types.InlineKeyboardButton("📊 Check Status", callback_data="check_status")
        )
        keyboard.row(
            types.InlineKeyboardButton("🔗 Group Links", callback_data="group_links"),
            types.InlineKeyboardButton("❓ Help", callback_data="help")
        )
        
        # Send with shield animation
        shield_msg = self.bot.send_message(message.chat.id, "🛡️")
        self.bot.delete_message(message.chat.id, shield_msg.message_id)
        
        self.bot.send_message(
            message.chat.id,
            welcome_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def handle_escrow_start(self, message):
        """Handle /escrow command to start new transaction"""
        user_id = message.from_user.id
        self.user_sessions[user_id] = {'state': 'selecting_amount'}
        self.show_amount_selection(message.chat.id)
    
    def show_amount_selection(self, chat_id):
        """Show amount selection with animated buttons"""
        text = """
💰 **Select Escrow Amount**

Choose from quick options below or enter a custom amount:
        """
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("💰 Rs. 100", callback_data="amount_100"),
            types.InlineKeyboardButton("💵 Rs. 500", callback_data="amount_500")
        )
        keyboard.row(
            types.InlineKeyboardButton("💎 Rs. 1000", callback_data="amount_1000"),
            types.InlineKeyboardButton("📝 Custom Amount", callback_data="amount_custom")
        )
        keyboard.row(
            types.InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        )
        
        self.bot.send_message(
            chat_id,
            text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def create_transaction(self, user_id: int, username: str, amount: int) -> Optional[str]:
        """Create a new transaction via API"""
        try:
            data = {
                'telegramUserId': str(user_id),
                'telegramUsername': username,
                'amount': amount,
                'paymentMethod': 'upi'
            }
            
            response = requests.post(f"{self.api_base_url}/transactions", json=data)
            if response.status_code == 200:
                transaction = response.json()
                return transaction
            else:
                logger.error(f"Failed to create transaction: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            return None
    
    def generate_qr_code(self, upi_data: str):
        """Generate QR code for UPI payment"""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(upi_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to BytesIO for sending
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            return img_buffer
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None
    
    def show_payment_qr(self, chat_id: int, transaction: dict):
        """Show QR code for payment with loading animation"""
        # Loading animation
        loading_msg = self.bot.send_message(chat_id, "⏳ Generating QR Code...")
        
        # Simulate loading
        for i in range(3):
            try:
                self.bot.edit_message_text(
                    f"⏳ Generating QR Code{'.' * (i + 1)}",
                    chat_id,
                    loading_msg.message_id
                )
                import time
                time.sleep(0.5)
            except:
                pass
        
        self.bot.delete_message(chat_id, loading_msg.message_id)
        
        # Generate QR code
        qr_buffer = self.generate_qr_code(transaction['qrCodeData'])
        
        if qr_buffer:
            # Payment instructions
            payment_text = f"""
💳 **Scan to Pay!**

🔹 **Amount:** Rs. {transaction['amount']}
🔹 **UPI ID:** {self.upi_id}
🔹 **Transaction ID:** {transaction['transactionId']}

📱 Scan the QR code below to complete payment:
            """
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(
                types.InlineKeyboardButton("✅ Payment Done", callback_data=f"payment_done_{transaction['id']}"),
                types.InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            )
            
            # Send QR code
            self.bot.send_photo(
                chat_id,
                qr_buffer,
                caption=payment_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            self.bot.send_message(
                chat_id,
                "❌ Failed to generate QR code. Please try again.",
                reply_markup=types.InlineKeyboardMarkup().row(
                    types.InlineKeyboardButton("🔄 Retry", callback_data="start_escrow")
                )
            )
    
    def verify_payment(self, transaction_id: str) -> bool:
        """Verify payment status (simulated)"""
        # In a real implementation, this would check with payment gateway
        # For demo purposes, we'll simulate 80% success rate
        import random
        return random.random() > 0.2
    
    def update_transaction_status(self, transaction_id: int, status: str) -> bool:
        """Update transaction status via API"""
        try:
            data = {'status': status}
            response = requests.patch(f"{self.api_base_url}/transactions/{transaction_id}", json=data)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error updating transaction: {e}")
            return False
    
    def show_payment_result(self, chat_id: int, success: bool, transaction: dict):
        """Show payment result with animation"""
        if success:
            # Success animation
            for emoji in ["✅", "🎉", "✨"]:
                msg = self.bot.send_message(chat_id, emoji)
                asyncio.sleep(0.3)
                self.bot.delete_message(chat_id, msg.message_id)
            
            success_text = f"""
✅ **Payment Successful!**

🎉 Your escrow transaction is now active! ✨

**Transaction Details:**
• Amount: Rs. {transaction['amount']}
• Status: Escrowed
• Transaction ID: {transaction['transactionId']}
• Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Thank you for using QuickEscrowBot! 🛡️
            """
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(
                types.InlineKeyboardButton("🔄 New Transaction", callback_data="start_escrow"),
                types.InlineKeyboardButton("📊 View Status", callback_data="check_status")
            )
            
        else:
            fail_text = """
❌ **Payment Failed**

Sorry, we couldn't verify your payment. Please try again or contact support.

Possible reasons:
• Payment amount mismatch
• Network connectivity issues
• Payment gateway timeout

You can retry the payment or contact our support team.
            """
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(
                types.InlineKeyboardButton("🔄 Retry Payment", callback_data="start_escrow"),
                types.InlineKeyboardButton("📞 Contact Support", callback_data="support")
            )
        
        self.bot.send_message(
            chat_id,
            success_text if success else fail_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def handle_callback(self, call):
        """Handle inline keyboard callbacks"""
        user_id = call.from_user.id
        data = call.data
        chat_id = call.message.chat.id
        
        try:
            self.bot.answer_callback_query(call.id)
            
            if data == "start_escrow":
                self.user_sessions[user_id] = {'state': 'selecting_amount'}
                self.show_amount_selection(chat_id)
            
            elif data.startswith("amount_"):
                if data == "amount_custom":
                    self.user_sessions[user_id]['state'] = 'entering_custom_amount'
                    self.bot.send_message(
                        chat_id,
                        "📝 Please enter the amount in Rs. (e.g., 750):"
                    )
                else:
                    amount = int(data.split("_")[1])
                    self.process_amount_selection(chat_id, user_id, amount)
            
            elif data.startswith("payment_done_"):
                transaction_id = int(data.split("_")[2])
                self.process_payment_verification(chat_id, user_id, transaction_id)
            
            elif data == "cancel":
                self.handle_start(call.message)
            
            elif data == "check_status":
                self.handle_status_check(call.message)
            
            elif data == "group_links":
                self.show_group_links(chat_id)
            
            elif data == "help":
                self.handle_help(call.message)
            
            elif data == "support":
                self.show_support_info(chat_id)
        
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            self.bot.send_message(chat_id, "❌ An error occurred. Please try again.")
    
    def process_amount_selection(self, chat_id: int, user_id: int, amount: int):
        """Process the selected amount and create transaction"""
        username = self.user_sessions[user_id].get('username', 'User')
        
        # Create transaction
        transaction = self.create_transaction(user_id, username, amount)
        
        if transaction:
            self.user_sessions[user_id]['transaction'] = transaction
            self.show_payment_qr(chat_id, transaction)
        else:
            self.bot.send_message(
                chat_id,
                "❌ Failed to create transaction. Please try again.",
                reply_markup=types.InlineKeyboardMarkup().row(
                    types.InlineKeyboardButton("🔄 Retry", callback_data="start_escrow")
                )
            )
    
    def process_payment_verification(self, chat_id: int, user_id: int, transaction_id: int):
        """Process payment verification"""
        # Simulate payment verification
        success = self.verify_payment(str(transaction_id))
        
        # Update transaction status
        status = "completed" if success else "failed"
        self.update_transaction_status(transaction_id, status)
        
        # Get transaction details
        transaction = self.user_sessions[user_id].get('transaction', {})
        
        # Show result
        self.show_payment_result(chat_id, success, transaction)
    
    def handle_message(self, message):
        """Handle regular text messages"""
        user_id = message.from_user.id
        
        if user_id in self.user_sessions:
            state = self.user_sessions[user_id].get('state')
            
            if state == 'entering_custom_amount':
                try:
                    amount = int(message.text)
                    if amount > 0:
                        self.process_amount_selection(message.chat.id, user_id, amount)
                    else:
                        self.bot.send_message(
                            message.chat.id,
                            "❌ Please enter a valid amount greater than 0."
                        )
                except ValueError:
                    self.bot.send_message(
                        message.chat.id,
                        "❌ Please enter a valid number."
                    )
        else:
            # Default response for unrecognized messages
            self.bot.send_message(
                message.chat.id,
                "👋 Hi! Use /start to begin or /help for assistance."
            )
    
    def handle_status_check(self, message):
        """Handle status check request"""
        user_id = message.from_user.id
        
        # Get user's recent transactions
        try:
            response = requests.get(f"{self.api_base_url}/transactions")
            if response.status_code == 200:
                transactions = response.json()
                user_transactions = [t for t in transactions if t['telegramUserId'] == str(user_id)]
                
                if user_transactions:
                    status_text = "📊 **Your Recent Transactions:**\n\n"
                    for txn in user_transactions[:5]:  # Show last 5
                        status_emoji = {
                            'pending': '⏳',
                            'completed': '✅',
                            'failed': '❌'
                        }.get(txn['status'], '⚪')
                        
                        status_text += f"{status_emoji} **{txn['transactionId']}**\n"
                        status_text += f"   Amount: Rs. {txn['amount']}\n"
                        status_text += f"   Status: {txn['status'].title()}\n"
                        status_text += f"   Date: {txn['createdAt'][:10]}\n\n"
                else:
                    status_text = "📊 No transactions found.\n\nUse /escrow to start your first transaction!"
            else:
                status_text = "❌ Unable to fetch transaction status. Please try again later."
        except Exception as e:
            logger.error(f"Error fetching status: {e}")
            status_text = "❌ Unable to fetch transaction status. Please try again later."
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("🚀 New Transaction", callback_data="start_escrow"),
            types.InlineKeyboardButton("🏠 Main Menu", callback_data="cancel")
        )
        
        self.bot.send_message(
            message.chat.id,
            status_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def handle_help(self, message):
        """Handle help request"""
        help_text = """
❓ **QuickEscrowBot Help**

**Available Commands:**
• `/start` - Welcome message and main menu
• `/escrow` - Start new escrow transaction
• `/status` - Check your transaction status
• `/help` - Show this help message

**How it works:**
1️⃣ Choose an amount or enter custom amount
2️⃣ Scan the QR code to make payment
3️⃣ Confirm payment completion
4️⃣ Funds are held securely in escrow

**Features:**
🛡️ Secure encrypted transactions
⚡ Instant QR code generation
🤖 24/7 automated service
📱 Real-time payment verification

**Need Support?**
Contact: @quickescrow_support
        """
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("🚀 Start Transaction", callback_data="start_escrow"),
            types.InlineKeyboardButton("🏠 Main Menu", callback_data="cancel")
        )
        
        self.bot.send_message(
            message.chat.id,
            help_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def show_group_links(self, chat_id: int):
        """Show available group links"""
        try:
            response = requests.get(f"{self.api_base_url}/group-links")
            if response.status_code == 200:
                links = response.json()
                active_links = [link for link in links if link.get('isActive', True)]
                
                if active_links:
                    links_text = "🔗 **Available Group Links:**\n\n"
                    keyboard = types.InlineKeyboardMarkup()
                    
                    for link in active_links:
                        links_text += f"• {link['name']}\n"
                        keyboard.row(
                            types.InlineKeyboardButton(
                                f"📱 {link['name']}", 
                                url=link['url']
                            )
                        )
                    
                    keyboard.row(
                        types.InlineKeyboardButton("🏠 Main Menu", callback_data="cancel")
                    )
                else:
                    links_text = "🔗 No group links available at the moment."
                    keyboard = types.InlineKeyboardMarkup()
                    keyboard.row(
                        types.InlineKeyboardButton("🏠 Main Menu", callback_data="cancel")
                    )
            else:
                links_text = "❌ Unable to fetch group links."
                keyboard = types.InlineKeyboardMarkup()
                keyboard.row(
                    types.InlineKeyboardButton("🏠 Main Menu", callback_data="cancel")
                )
        except Exception as e:
            logger.error(f"Error fetching group links: {e}")
            links_text = "❌ Unable to fetch group links."
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(
                types.InlineKeyboardButton("🏠 Main Menu", callback_data="cancel")
            )
        
        self.bot.send_message(
            chat_id,
            links_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def show_support_info(self, chat_id: int):
        """Show support contact information"""
        support_text = """
📞 **Contact Support**

For assistance with your transactions or any issues:

**Support Channels:**
• Telegram: @quickescrow_support
• Email: support@quickescrow.com
• Website: https://quickescrow.com/support

**Business Hours:**
• Monday - Friday: 9:00 AM - 6:00 PM
• Saturday: 10:00 AM - 4:00 PM
• Sunday: Closed

**Emergency Support:**
Available 24/7 for critical transaction issues

We're here to help! 🛡️
        """
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("📱 Contact Support", url="https://t.me/quickescrow_support"),
            types.InlineKeyboardButton("🏠 Main Menu", callback_data="cancel")
        )
        
        self.bot.send_message(
            chat_id,
            support_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def run(self):
        """Start the bot"""
        logger.info("QuickEscrowBot starting...")
        try:
            self.bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            logger.error(f"Bot error: {e}")
            raise

if __name__ == "__main__":
    try:
        bot = QuickEscrowBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
