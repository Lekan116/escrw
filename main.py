import os
import sqlite3
import requests
import threading
from flask import Flask, request
import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "secretpath")  # new env var for webhook security

ASSET_WALLETS = {
    'BTC': os.getenv("BTC_WALLET"),
    'LTC': os.getenv("LTC_WALLET"),
    'USDT': os.getenv("USDT_WALLET"),
    'ETH': os.getenv("ETH_WALLET")
}

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
lock = threading.Lock()  # Thread-safe DB access

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

def main_menu():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Start Escrow", callback_data="start_escrow"),
        InlineKeyboardButton("Check Status", callback_data="status")
    )
    markup.row(
        InlineKeyboardButton("Help", callback_data="help"),
        InlineKeyboardButton("Terms", callback_data="terms")
    )
    return markup

@bot.message_handler(commands=['start'])
def start_command(message: Message):
    text = (
        "👋 *Hey there!*\n"
        "I'm your *Group Escrow Bot*.\n"
        "Tap buttons below or use /menu."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    handlers = {
        "start_escrow": begin_escrow,
        "status": view_status,
        "help": help_command,
        "terms": terms
    }
    if call.data in handlers:
        handlers[call.data](call.message)

@bot.message_handler(commands=['menu'])
def show_menu(message: Message):
    bot.send_message(message.chat.id, "📜 *Escrow Menu* – Use buttons or commands below:", parse_mode='Markdown', reply_markup=main_menu())

@bot.message_handler(commands=['terms'])
def terms(message: Message):
    bot.reply_to(message, "📜 *Escrow Terms:*\n- Both parties must register\n- Admin can resolve\n- Use wisely.", parse_mode='Markdown')

@bot.message_handler(commands=['about'])
def about(message: Message):
    bot.reply_to(message, "🤖 *P2P Escrow Bot*\nCreated by @streaks100", parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message: Message):
    bot.reply_to(message, "🆘 Use /beginescrow to start\nUse /menu for commands\nAdmin resolves disputes", parse_mode='Markdown')

@bot.message_handler(commands=['beginescrow'])
def begin_escrow(message: Message):
    group_id = message.chat.id
    with lock:
        cursor.execute("REPLACE INTO group_escrows (group_id, status) VALUES (?, ?)", (group_id, 'initiated'))
        conn.commit()
    bot.reply_to(message, "🔐 Escrow started! Use /seller and /buyer.")

@bot.message_handler(commands=['seller'])
def register_seller(message: Message):
    parts = message.text.split()
    if len(parts) != 2:
        return bot.reply_to(message, "⚠️ Usage: /seller wallet_address")
    wallet = parts[1]
    with lock:
        cursor.execute("UPDATE group_escrows SET seller_id=?, seller_wallet=? WHERE group_id=?", 
                       (message.from_user.id, wallet, message.chat.id))
        conn.commit()
    bot.reply_to(message, f"✅ Seller registered.\nWallet: `{wallet}`", parse_mode='Markdown')

@bot.message_handler(commands=['buyer'])
def register_buyer(message: Message):
    parts = message.text.split()
    if len(parts) != 2:
        return bot.reply_to(message, "⚠️ Usage: /buyer wallet_address")
    wallet = parts[1]
    with lock:
        cursor.execute("UPDATE group_escrows SET buyer_id=?, buyer_wallet=? WHERE group_id=?", 
                       (message.from_user.id, wallet, message.chat.id))
        conn.commit()
    bot.reply_to(message, f"✅ Buyer registered.\nWallet: `{wallet}`", parse_mode='Markdown')

@bot.message_handler(commands=['asset'])
def choose_asset(message: Message):
    parts = message.text.split()
    if len(parts) != 2:
        return bot.reply_to(message, f"⚠️ Usage: /asset COIN\nOptions: {', '.join(ASSET_WALLETS)}")
    asset = parts[1].upper()
    if asset not in ASSET_WALLETS:
        return bot.reply_to(message, f"❌ Invalid asset. Options: {', '.join(ASSET_WALLETS)}")
    with lock:
        cursor.execute("UPDATE group_escrows SET asset=? WHERE group_id=?", (asset, message.chat.id))
        conn.commit()
    bot.reply_to(message, f"💰 Asset: {asset}\nSend to:\n`{ASSET_WALLETS[asset]}`", parse_mode='Markdown')

def get_balance(asset, address):
    try:
        if asset in ['BTC', 'LTC']:
            url = f"https://sochain.com/api/v2/get_address_balance/{asset}/{address}"
            res = requests.get(url).json()
            if res['status'] == 'success':
                return res['data']['confirmed_balance']
        elif asset in ['ETH', 'USDT']:
            if asset == 'USDT':
                contract = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
                url = f"https://api.etherscan.io/api?module=account&action=tokenbalance&contractaddress={contract}&address={address}&tag=latest&apikey={ETHERSCAN_API_KEY}"
                decimals = 1e6
            else:
                url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={ETHERSCAN_API_KEY}"
                decimals = 1e18
            res = requests.get(url).json()
            if res.get('status') == '1':
                return str(int(res['result']) / decimals)
    except:
        pass
    return None

@bot.message_handler(commands=['balance'])
def check_balance(message: Message):
    with lock:
        cursor.execute("SELECT asset, buyer_wallet FROM group_escrows WHERE group_id=?", (message.chat.id,))
        row = cursor.fetchone()
    if not row or not row[0] or not row[1]:
        return bot.reply_to(message, "⚠️ Asset or buyer wallet not set.")
    balance = get_balance(row[0], row[1])
    if not balance:
        return bot.reply_to(message, f"❌ Failed to fetch {row[0]} balance.")
    bot.reply_to(message, f"📦 *{row[0]} Balance*\n`{row[1]}`\n💰 {balance}", parse_mode='Markdown')

@bot.message_handler(commands=['releasefund'])
def release_funds(message: Message):
    with lock:
        cursor.execute("SELECT seller_wallet, asset FROM group_escrows WHERE group_id=?", (message.chat.id,))
        row = cursor.fetchone()
    if row and row[0] and row[1]:
        bot.reply_to(message, f"✅ Released to seller:\n`{row[0]}`\nAsset: *{row[1]}*", parse_mode='Markdown')

@bot.message_handler(commands=['adminresolve'])
def admin_force_release(message: Message):
    if message.from_user.id == ADMIN_ID:
        with lock:
            cursor.execute("DELETE FROM group_escrows WHERE group_id=?", (message.chat.id,))
            conn.commit()
        bot.reply_to(message, "🛑 Admin resolved the session.")
    else:
        bot.reply_to(message, "⛔ Only admin allowed.")

@bot.message_handler(commands=['status'])
def view_status(message: Message):
    with lock:
        cursor.execute("SELECT buyer_wallet, seller_wallet, asset, status FROM group_escrows WHERE group_id=?", (message.chat.id,))
        row = cursor.fetchone()
    if row:
        bot.reply_to(message, f"📊 *Status*\nBuyer: `{row[0]}`\nSeller: `{row[1]}`\nAsset: *{row[2]}*\nStatus: *{row[3]}*", parse_mode='Markdown')
    else:
        bot.reply_to(message, "ℹ️ No active session.")

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text.startswith("!send"))
def admin_broadcast(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return bot.reply_to(message, "⚠️ Usage: !send group_id message")
    try:
        group_id = int(parts[1])
        bot.send_message(group_id, parts[2])
        bot.reply_to(message, f"✅ Message sent to {group_id}")
    except Exception as e:
        bot.reply_to(message, f"❌ Failed: {e}")

@app.route('/', methods=['GET'])
def index():
    return 'Bot running!', 200

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_json())
    bot.process_new_updates([update])
    return '', 200

# Set webhook
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
bot.remove_webhook()
bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")

if __name__ == '__main__':
    import atexit
    atexit.register(lambda: conn.close())  # graceful shutdown
    port = int(os.environ.get('PORT', 8080))
    app.run(host="0.0.0.0", port=port)
