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
    markup.row("\ud83d\udcbc Start Escrow", "\ud83d\udcd6 Help & Commands")
    markup.row("\ud83d\udcdc Terms", "\ud83d\udd12 Escrow Status")

    welcome_text = (
        "\ud83e\udd16 *Welcome to P2P Escrow Bot!*\n\n"
        "This bot helps you complete safe and secure crypto deals using escrow.\n"
        "Start a deal, verify wallets, and get admin help if needed.\n\n"
        "*\ud83d\udd10 100% Transparency*\n"
        "*\u2696\ufe0f Admin Conflict Resolution*\n"
        "*\ud83d\udcb0 Fast, Secure Releases*\n\n"
        "Use the buttons below or type /help to view all available commands."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='Markdown')

# === PERSISTENT COMMAND MENU ===
def set_bot_commands():
    commands = [
        telebot.types.BotCommand("start", "Show start menu"),
        telebot.types.BotCommand("help", "List all commands"),
        telebot.types.BotCommand("escrow", "Start a new escrow deal"),
        telebot.types.BotCommand("confirm", "Confirm release of funds"),
        telebot.types.BotCommand("cancel", "Cancel an ongoing deal"),
        telebot.types.BotCommand("status", "Check your current deal"),
        telebot.types.BotCommand("verifyescrow", "Check wallet trust"),
        telebot.types.BotCommand("terms", "View terms and disclaimer"),
        telebot.types.BotCommand("adminresolve", "(Admin only) Force release"),
    ]
    bot.set_my_commands(commands)

# === HELP COMMAND ===
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
\ud83d\udcd6 *ESCROW BOT COMMANDS*:
/start - Show menu
/help - Show help message
/escrow - Start a new escrow session
/confirm - Confirm the deal
/cancel - Cancel an active escrow
/status - View current escrow status
/verifyescrow - Check if wallet is valid
/terms - View terms and disclaimer
/adminresolve - (Admin only)
"""
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# === TERMS COMMAND ===
@bot.message_handler(commands=['terms'])
def send_terms(message):
    terms_text = """
\ud83d\udcdc *TERMS & CONDITIONS*:
- Escrow bot is for P2P deals.
- Funds must be confirmed before release.
- Admin can resolve disputes.
- We do not guarantee recovery of lost funds.
"""
    bot.send_message(message.chat.id, terms_text, parse_mode='Markdown')

# === ESCROW COMMANDS ===
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
        return bot.reply_to(message, "\u274c You're not authorized.")
    cursor.execute("DELETE FROM escrows WHERE chat_id = ?", (message.chat.id,))
    conn.commit()
    bot.send_message(message.chat.id, "\ud83d\udd13 Admin manually resolved and closed the escrow.")

# === FORWARD NON-COMMANDS TO ADMIN ===
@bot.message_handler(func=lambda msg: not msg.text.startswith('/'))
def forward_all(message):
    try:
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    except Exception as e:
        print(f"Failed to forward message: {e}")

# === START BOT ===
if __name__ == '__main__':
    set_bot_commands()
    keep_alive()
    bot.polling()
