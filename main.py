import os
import sqlite3
import telebot
from dotenv import load_dotenv
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# === ENV & INIT ===
load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Dynamically load asset wallets from .env
ASSET_WALLETS = {
    key.split('_')[0]: os.getenv(key) for key in os.environ if key.endswith('_WALLET')
}

# === DATABASE SETUP ===
conn = sqlite3.connect("group_escrow.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS group_escrows (
        group_id INTEGER PRIMARY KEY,
        buyer_id INTEGER,
        seller_id INTEGER,
        buyer_wallet TEXT,
        seller_wallet TEXT,
        asset TEXT,
        status TEXT
    )
''')
conn.commit()

# === MENU ===
@bot.message_handler(commands=['menu'])
def show_menu(message: Message):
    menu_text = (
        "📜 *Escrow Bot Menu*\n"
        "/beginescrow – Start a new group escrow\n"
        "/seller @username wallet – Register seller\n"
        "/buyer @username wallet – Register buyer\n"
        "/asset COIN – Choose asset (e.g. /asset BTC)\n"
        "/balance – Check current asset set\n"
        "/releasefund – Release funds to seller\n"
        "/adminresolve – Force resolve (Admin only)\n"
        "/terms – View escrow terms\n"
        "/about – About this bot\n"
        "/help – Command help"
    )
    bot.reply_to(message, menu_text, parse_mode='Markdown')

# === TERMS / ABOUT / HELP ===
@bot.message_handler(commands=['terms'])
def show_terms(message: Message):
    bot.reply_to(message, (
        "📜 *Escrow Terms & Conditions:*\n"
        "- Buyer & seller must be registered.\n"
        "- Asset must be chosen before funding.\n"
        "- Admin may resolve disputes manually.\n"
        "- Funds are manually released via /releasefund.\n"
        "- This bot does not handle actual funds.\n"
        "- Use commands inside the group only."
    ), parse_mode='Markdown')

@bot.message_handler(commands=['about'])
def about(message: Message):
    bot.reply_to(message, (
        "🤖 *Group Escrow Bot v1.0*\n"
        "Designed for Telegram groups to safely manage P2P trades using manual escrow control.\n"
        "Built by @blitz_gng for secure group transactions."
    ), parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_cmd(message: Message):
    bot.reply_to(message, (
        "🆘 *Help Guide:*\n"
        "1. /beginescrow – Start the session\n"
        "2. /seller @user wallet – Register seller\n"
        "3. /buyer @user wallet – Register buyer\n"
        "4. /asset BTC – Choose asset (based on .env wallets)\n"
        "5. /releasefund – Release to seller manually\n"
        "6. /adminresolve – Admin can force-clear escrow\n\n"
        "Use /menu for full command list."
    ), parse_mode='Markdown')

# === BEGIN ESCROW ===
@bot.message_handler(commands=['beginescrow'])
def begin_escrow(message: Message):
    group_id = message.chat.id
    cursor.execute("REPLACE INTO group_escrows (group_id, status) VALUES (?, ?)", (group_id, 'initiated'))
    conn.commit()
    bot.reply_to(message, "🔐 Escrow started. Use /seller and /buyer to register parties.")

# === REGISTER SELLER ===
@bot.message_handler(commands=['seller'])
def set_seller(message: Message):
    parts = message.text.split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /seller @username wallet_address")
    group_id = message.chat.id
    seller_wallet = parts[2]
    cursor.execute("UPDATE group_escrows SET seller_id = ?, seller_wallet = ? WHERE group_id = ?",
                   (message.from_user.id, seller_wallet, group_id))
    conn.commit()
    bot.reply_to(message, f"✅ Seller registered: {parts[1]}\nWallet: `{seller_wallet}`", parse_mode='Markdown')

# === REGISTER BUYER ===
@bot.message_handler(commands=['buyer'])
def set_buyer(message: Message):
    parts = message.text.split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /buyer @username wallet_address")
    group_id = message.chat.id
    buyer_wallet = parts[2]
    cursor.execute("UPDATE group_escrows SET buyer_id = ?, buyer_wallet = ? WHERE group_id = ?",
                   (message.from_user.id, buyer_wallet, group_id))
    conn.commit()
    bot.reply_to(message, f"✅ Buyer registered: {parts[1]}\nWallet: `{buyer_wallet}`", parse_mode='Markdown')

# === SELECT ASSET ===
@bot.message_handler(commands=['asset', 'choose'])
def choose_asset(message: Message):
    parts = message.text.split()
    if len(parts) != 2:
        available = ', '.join(ASSET_WALLETS.keys())
        return bot.reply_to(message, f"⚠️ Usage: /asset COIN\nAvailable: {available}")
    asset = parts[1].upper()
    if asset not in ASSET_WALLETS:
        return bot.reply_to(message, f"❌ Invalid asset. Available: {', '.join(ASSET_WALLETS.keys())}")
    group_id = message.chat.id
    cursor.execute("UPDATE group_escrows SET asset = ? WHERE group_id = ?", (asset, group_id))
    conn.commit()
    bot.reply_to(message, f"💰 Asset set to *{asset}*\nSend funds to: `{ASSET_WALLETS[asset]}`", parse_mode='Markdown')

# === BALANCE ===
@bot.message_handler(commands=['balance'])
def check_asset(message: Message):
    group_id = message.chat.id
    cursor.execute("SELECT asset FROM group_escrows WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    if not row or not row[0]:
        return bot.reply_to(message, "❌ No asset selected yet.")
    asset = row[0]
    bot.reply_to(message, f"🧾 Escrow is set for *{asset}*", parse_mode='Markdown')

# === RELEASE FUNDS ===
@bot.message_handler(commands=['releasefund'])
def release(message: Message):
    group_id = message.chat.id
    cursor.execute("SELECT seller_wallet, asset FROM group_escrows WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    if not row or not row[0] or not row[1]:
        return bot.reply_to(message, "❌ Incomplete escrow setup.")
    wallet, asset = row
    bot.reply_to(message, f"✅ Funds released to seller:\nWallet: `{wallet}`\nAsset: *{asset}*", parse_mode='Markdown')

# === ADMIN RESOLVE ===
@bot.message_handler(commands=['adminresolve'])
def force_clear(message: Message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Admin only.")
    group_id = message.chat.id
    cursor.execute("DELETE FROM group_escrows WHERE group_id = ?", (group_id,))
    conn.commit()
    bot.reply_to(message, "🛑 Escrow forcibly resolved by admin.")

# === START ===
bot.infinity_polling()
