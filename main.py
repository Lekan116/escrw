import os
import sqlite3
from flask import Flask, request
import telebot
from telebot.types import Message
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

ASSET_WALLETS = {
    'BTC': os.getenv("BTC_WALLET"),
    'LTC': os.getenv("LTC_WALLET"),
    'USDT': os.getenv("USDT_WALLET"),
    'ETH': os.getenv("ETH_WALLET")
}

# === Init bot and flask ===
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === DB Setup ===
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

# === Commands ===
@bot.message_handler(commands=['menu'])
def show_menu(message: Message):
    menu = (
        "📜 *Escrow Menu*\n"
        "/beginescrow – Start group escrow\n"
        "/seller @username wallet – Register seller\n"
        "/buyer @username wallet – Register buyer\n"
        "/asset COIN – Choose asset\n"
        "/balance – Check balance\n"
        "/releasefund – Release funds\n"
        "/adminresolve – Admin force resolve\n"
        "/terms – View terms\n"
        "/about – About bot\n"
        "/help – Get help"
    )
    bot.reply_to(message, menu, parse_mode='Markdown')

@bot.message_handler(commands=['terms'])
def terms(message: Message):
    terms = (
        "📜 *Escrow Terms:*\n"
        "- Both buyer & seller must register\n"
        "- Select asset before funding\n"
        "- Admin can resolve disputes\n"
        "- Escrow bot not liable for losses"
    )
    bot.reply_to(message, terms, parse_mode='Markdown')

@bot.message_handler(commands=['about'])
def about(message: Message):
    bot.reply_to(message,
        "🤖 *P2P Escrow Bot*\nCreated by @streaks100.\nManual fund release with safe admin fallback.",
        parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message: Message):
    text = (
        "🆘 *Help Guide:*\n"
        "Start with /beginescrow\n"
        "Register seller and buyer\n"
        "Select /asset (e.g. LTC, BTC)\n"
        "Release using /releasefund\n"
        "Use /menu for full commands"
    )
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['beginescrow'])
def begin_escrow(message: Message):
    group_id = message.chat.id
    cursor.execute("REPLACE INTO group_escrows (group_id, status) VALUES (?, ?)", (group_id, 'initiated'))
    conn.commit()
    bot.reply_to(message, "🔐 Escrow started! Use /seller and /buyer to register.")

@bot.message_handler(commands=['seller'])
def register_seller(message: Message):
    parts = message.text.split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /seller @username wallet_address")
    seller_id = message.from_user.id
    wallet = parts[2]
    group_id = message.chat.id
    cursor.execute("UPDATE group_escrows SET seller_id = ?, seller_wallet = ? WHERE group_id = ?", (seller_id, wallet, group_id))
    conn.commit()
    bot.reply_to(message, f"✅ Seller set: {parts[1]}\nWallet: `{wallet}`", parse_mode='Markdown')

@bot.message_handler(commands=['buyer'])
def register_buyer(message: Message):
    parts = message.text.split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /buyer @username wallet_address")
    buyer_id = message.from_user.id
    wallet = parts[2]
    group_id = message.chat.id
    cursor.execute("UPDATE group_escrows SET buyer_id = ?, buyer_wallet = ? WHERE group_id = ?", (buyer_id, wallet, group_id))
    conn.commit()
    bot.reply_to(message, f"✅ Buyer set: {parts[1]}\nWallet: `{wallet}`", parse_mode='Markdown')

@bot.message_handler(commands=['asset', 'choose'])
def choose_asset(message: Message):
    parts = message.text.split()
    if len(parts) != 2:
        return bot.reply_to(message, f"⚠️ Usage: /asset COIN\nAvailable: {', '.join(ASSET_WALLETS)}")
    asset = parts[1].upper()
    if asset not in ASSET_WALLETS:
        return bot.reply_to(message, f"❌ Invalid asset. Available: {', '.join(ASSET_WALLETS)}")
    group_id = message.chat.id
    cursor.execute("UPDATE group_escrows SET asset = ? WHERE group_id = ?", (asset, group_id))
    conn.commit()
    bot.reply_to(message, f"💰 Asset selected: {asset}\n📥 Send funds to:\n`{ASSET_WALLETS[asset]}`", parse_mode='Markdown')

@bot.message_handler(commands=['balance'])
def check_balance(message: Message):
    group_id = message.chat.id
    cursor.execute("SELECT asset FROM group_escrows WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    if not row or not row[0]:
        return bot.reply_to(message, "⚠️ No asset selected yet. Use /asset first.")
    asset = row[0]
    bot.reply_to(message, f"🧾 Balance check for *{asset}*\n⏳ Coming soon...", parse_mode='Markdown')

@bot.message_handler(commands=['releasefund'])
def release_funds(message: Message):
    group_id = message.chat.id
    cursor.execute("SELECT seller_wallet, asset FROM group_escrows WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    if not row:
        return bot.reply_to(message, "❌ No active escrow found.")
    seller_wallet, asset = row
    bot.reply_to(message, f"✅ Funds released to seller:\nWallet: `{seller_wallet}`\nAsset: *{asset}*", parse_mode='Markdown')

@bot.message_handler(commands=['adminresolve'])
def admin_force_release(message: Message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Only admin can do this.")
    group_id = message.chat.id
    cursor.execute("DELETE FROM group_escrows WHERE group_id = ?", (group_id,))
    conn.commit()
    bot.reply_to(message, "🛑 Admin force-resolved the escrow session.")

# === Webhook Setup ===
@app.route('/', methods=['GET'])
def index():
    return 'Escrow bot running!', 200

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_json())
    bot.process_new_updates([update])
    return '', 200

# === Start Webhook ===
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
bot.remove_webhook()
bot.set_webhook(WEBHOOK_URL)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host="0.0.0.0", port=port)
