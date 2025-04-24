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

# === USER COMMANDS ===

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🤖 Welcome to the Escrow Bot!\nUse /help to see commands.")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, """
📖 *ESCROW BOT COMMANDS*:
/start - Start the bot
/help - Show this help message
/escrow - Start a new escrow session
/confirm - Confirm deal to release funds
/cancel - Cancel an active escrow
/status - View current escrow status
/adminresolve - (Admin only) Manually resolve a deal
""", parse_mode='Markdown')

@bot.message_handler(commands=['escrow'])
def start_escrow(message):
    chat_id = message.chat.id
    if chat_id in escrows:
        bot.reply_to(message, "⚠️ Escrow already active. Use /status.")
    else:
        escrows[chat_id] = {"confirmed": [], "cancelled": False}
        bot.send_message(chat_id, f"✅ Escrow initiated!\n{get_wallets()}", parse_mode='Markdown')

@bot.message_handler(commands=['confirm'])
def confirm_deal(message):
    chat_id = message.chat.id
    user = message.from_user.id

    if chat_id not in escrows:
        bot.reply_to(message, "❌ No active escrow. Use /escrow.")
        return

    if user not in escrows[chat_id]["confirmed"]:
        escrows[chat_id]["confirmed"].append(user)

    if len(escrows[chat_id]["confirmed"]) >= 2:
        bot.send_message(chat_id, "✅ Both parties confirmed. Funds can be released.")
    else:
        bot.send_message(chat_id, "☑️ Confirmation received. Waiting for the other party.")

@bot.message_handler(commands=['cancel'])
def cancel_deal(message):
    chat_id = message.chat.id
    if chat_id not in escrows:
        bot.reply_to(message, "❌ No active escrow.")
        return

    escrows[chat_id]["cancelled"] = True
    bot.send_message(chat_id, "❌ Escrow cancelled by user.")

@bot.message_handler(commands=['status'])
def check_status(message):
    chat_id = message.chat.id
    if chat_id not in escrows:
        bot.reply_to(message, "ℹ️ No active escrow.")
        return

    escrow = escrows[chat_id]
    status_msg = f"""
🔒 *Escrow Status*:
- Confirmations: {len(escrow['confirmed'])}/2
- Cancelled: {'✅' if escrow['cancelled'] else '❌'}
"""
    bot.send_message(chat_id, status_msg, parse_mode='Markdown')

# === ADMIN SECTION ===

@bot.message_handler(commands=['adminresolve'])
def admin_resolve(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ You're not authorized.")

    chat_id = message.chat.id
    if chat_id in escrows:
        del escrows[chat_id]
        bot.send_message(chat_id, "🔓 Admin manually resolved and closed the escrow.")
    else:
        bot.send_message(chat_id, "❌ No escrow found.")

# === KEEP ALIVE ===
keep_alive()
bot.polling()
