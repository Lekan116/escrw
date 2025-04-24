import telebot
from dotenv import load_dotenv
import os
from keep_alive import keep_alive

# === ENV SETUP ===
load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# === ESCROW STORE ===
escrows = {}

# === WALLET FUNCTION ===
def get_wallets():
    return f"""
💼 *Send crypto to hold in escrow:*
- BTC: `{os.getenv("BTC_ADDRESS")}`
- LTC: `{os.getenv("LTC_ADDRESS")}`
- ETH: `{os.getenv("ETH_ADDRESS")}`
- USDT: `{os.getenv("USDT_ADDRESS")}`
"""

# === /start COMMAND ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, f"""
🤖 *Welcome to the Escrow Bot!*

This bot protects both buyer and seller in a deal by holding crypto funds safely until both sides confirm.

💡 Use /escrow to begin a new trade.

Type /help to see all commands.
""", parse_mode="Markdown")

# === /help COMMAND ===
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, """
📖 *ESCROW BOT COMMANDS*:
/start - Start the bot
/help - Show help message
/escrow - Start a new escrow session
/confirm - Confirm deal to release funds
/cancel - Cancel an active escrow
/status - View current escrow status
/adminresolve - (Admin only) Manually resolve a deal
""", parse_mode='Markdown')

# === USER: START ESCROW ===
@bot.message_handler(commands=['escrow'])
def start_escrow(message):
    chat_id = message.chat.id
    if chat_id in escrows:
        bot.reply_to(message, "⚠️ Escrow already active. Use /status to check.")
    else:
        escrows[chat_id] = {"confirmed": [], "cancelled": False}
        bot.send_message(chat_id, f"✅ Escrow initiated!\n{get_wallets()}", parse_mode='Markdown')

# === USER: CONFIRM ESCROW ===
@bot.message_handler(commands=['confirm'])
def confirm_deal(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id not in escrows:
        return bot.reply_to(message, "❌ No active escrow. Use /escrow to start one.")

    if user_id not in escrows[chat_id]["confirmed"]:
        escrows[chat_id]["confirmed"].append(user_id)

    if len(escrows[chat_id]["confirmed"]) >= 2:
        bot.send_message(chat_id, "✅ Both parties confirmed. Funds can now be released.")
    else:
        bot.send_message(chat_id, "☑️ Your confirmation received. Waiting for the other party.")

# === USER: CANCEL ESCROW ===
@bot.message_handler(commands=['cancel'])
def cancel_deal(message):
    chat_id = message.chat.id
    if chat_id not in escrows:
        return bot.reply_to(message, "❌ No active escrow found.")

    escrows[chat_id]["cancelled"] = True
    bot.send_message(chat_id, "❌ Escrow cancelled by user.")

# === USER: CHECK STATUS ===
@bot.message_handler(commands=['status'])
def check_status(message):
    chat_id = message.chat.id
    if chat_id not in escrows:
        return bot.reply_to(message, "ℹ️ No active escrow.")

    escrow = escrows[chat_id]
    status_msg = f"""
🔒 *Escrow Status*:
- Confirmations: {len(escrow['confirmed'])}/2
- Cancelled: {'✅' if escrow['cancelled'] else '❌'}
"""
    bot.send_message(chat_id, status_msg, parse_mode='Markdown')

# === ADMIN: MANUAL RESOLVE ===
@bot.message_handler(commands=['adminresolve'])
def admin_resolve(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ You're not authorized.")

    chat_id = message.chat.id
    if chat_id in escrows:
        del escrows[chat_id]
        bot.send_message(chat_id, "🔓 *Escrow manually resolved by admin.*", parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "❌ No escrow found.")

# === KEEP ALIVE + START BOT ===
keep_alive()
bot.polling()
