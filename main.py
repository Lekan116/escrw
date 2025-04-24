
import os
import sqlite3
import telebot
from dotenv import load_dotenv
from keep_alive import keep_alive
from utils import create_tables, get_wallets, create_escrow, confirm_escrow, cancel_escrow, get_status, verify_wallet

# === ENV SETUP ===
load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# === DATABASE SETUP ===
conn = sqlite3.connect("escrow.db", check_same_thread=False)
cursor = conn.cursor()
create_tables(cursor)

# === START MENU ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💼 Start Escrow", "📖 Help & Commands")
    markup.row("📜 Terms", "🔒 Escrow Status")
    bot.send_message(message.chat.id,
        f"🤖 Welcome to *Escrow Secure Bot*!\n\n" +
        "Use the menu below to begin a secure transaction.\n\n" +
        "For support or custom deals, contact admin.",
        reply_markup=markup,
        parse_mode='Markdown'
    )

# === HELP COMMAND ===
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, """
📖 *ESCROW BOT COMMANDS*:
/start - Show menu
/help - Show help message
/escrow - Start a new escrow session
/confirm - Confirm the deal
/cancel - Cancel an active escrow
/status - View current escrow status
/verifyescrow - Check if wallet is valid
/terms - View terms and disclaimer
/adminresolve - (Admin only)
""", parse_mode='Markdown')

# === TERMS COMMAND ===
@bot.message_handler(commands=['terms'])
def send_terms(message):
    bot.send_message(message.chat.id, """
📜 *TERMS & CONDITIONS*:
- Escrow bot is for P2P deals.
- Funds must be confirmed before release.
- Admin can resolve disputes.
- We do not guarantee recovery of lost funds.
""", parse_mode='Markdown')

# === ESCROW COMMAND ===
@bot.message_handler(commands=['escrow'])
def escrow_handler(message):
    create_escrow(message, cursor, conn, bot)

@bot.message_handler(commands=['confirm'])
def confirm_handler(message):
    confirm_escrow(message, cursor, conn, bot)

@bot.message_handler(commands=['cancel'])
def cancel_handler(message):
    cancel_escrow(message, cursor, conn, bot)

@bot.message_handler(commands=['status'])
def status_handler(message):
    get_status(message, cursor, bot)

@bot.message_handler(commands=['verifyescrow'])
def verify_handler(message):
    verify_wallet(message, bot)

# === ADMIN RESOLVE ===
@bot.message_handler(commands=['adminresolve'])
def admin_resolve(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ You're not authorized.")
    cursor.execute("DELETE FROM escrows WHERE chat_id = ?", (message.chat.id,))
    conn.commit()
    bot.send_message(message.chat.id, "🔓 Admin manually resolved and closed the escrow.")

# === START BOT ===
keep_alive()
bot.polling()
