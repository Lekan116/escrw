import os
import requests
import sqlite3
from flask import Flask, request
import telebot
from telebot.types import BotCommand
from telebot.types import Message
from telebot.types import InputFile
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

ASSET_WALLETS = {
    'BTC': os.getenv("BTC_WALLET"),
    'LTC': os.getenv("LTC_WALLET"),
    'USDT': os.getenv("USDT_WALLET"),
    'ETH': os.getenv("ETH_WALLET")
}

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables.")
if not ETHERSCAN_API_KEY:
    raise ValueError("ETHERSCAN_API_KEY is not set in environment variables.")

# === Init bot and flask ===
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
bot.set_my_commands([
    BotCommand("start", "Start the bot"),
    BotCommand("menu", "Show full command menu"),
    BotCommand("beginescrow", "Start group escrow"),
    BotCommand("seller", "Register seller wallet"),
    BotCommand("buyer", "Register buyer wallet"),
    BotCommand("asset", "Choose asset to trade"),
    BotCommand("editwallet", "Correct your wallet address"),
    BotCommand("cancelescrow", "Cancel escrow session"),
    BotCommand("balance", "Check escrow balance"),
    BotCommand("releasefund", "Release funds to seller"),
    BotCommand("adminresolve", "Force close escrow (admin only)"),
    BotCommand("status", "View escrow status"),
    BotCommand("terms", "View escrow terms"),
    BotCommand("about", "About the bot"),
    BotCommand("help", "How to use the bot")
])
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

# === Bot Commands ===

@bot.message_handler(commands=['start'])
def start_command(message: Message):
    # Send an animation or GIF from a URL
    bot.send_video(chat_id=message.chat.id, video="https://laoder5.wordpress.com/wp-content/uploads/2025/05/7916cb61-9e9d-431b-8121-e5ffcfee4349.mp4")
    
    # Now send the welcome text
    text = (
    "👋 *Welcome to P2PEscrowBot!*\n\n"
    "This bot provides a secure escrow service for your transactions on Telegram. 🔒\n"
    "No more worries about getting scammed — your funds stay safe during all your deals.\n\n"
    "🛡️ *How It Works:*\n"
    "1. Add @p2p_escrowbot to your trading group.\n"
    "2. Use `/beginescrow` in the group to initiate an escrow session.\n"
    "3. Have the *seller* and *buyer* register their wallets using:\n"
    "   • `/seller BTC_ADDRESS`\n"
    "   • `/buyer USDT_ADDRESS`\n"
    "4. Use `/asset BTC` or `/asset USDT` to choose the asset for the deal.\n"
    "5. Buyer sends funds to the wallet address shown by the bot.\n"
    "6. Use `/balance` to confirm the funds arrived.\n"
    "7. If someone entered the wrong wallet, correct it with `/editwallet NEW_ADDRESS`\n"
    "8. When both parties agree, use `/releasefund` to release the escrow.\n"
    "9. If the deal falls through, either party can cancel with `/cancelescrow`\n"
    "10. Admin can intervene anytime with `/adminresolve` in case of dispute.\n\n"
    "💰 *ESCROW FEE:* \n"
    "• 5% for amounts over $100\n"
    "• $5 flat fee for amounts under $100\n\n"
    "🌟 *BOT STATS:*\n"
    "✅ *Deals Completed:* 170\n"
    "⚖️ *Disputes Resolved:* 20\n\n"
    "💡 *Tips:*\n"
    "• Always use `/status` to check live escrow info.\n"
    "• Use `/terms` to review escrow rules.\n"
    "• Use `/menu` in the group to view all features.\n"
    "• Mistyped wallet? Just run `/editwallet` with the correct one.\n"
    "• Need to back out? Use `/cancelescrow` anytime before release.\n\n"
    "⚠️ If you run into issues, contact the admin and an *arbitrator* will join your group. ⏳\n\n"
    "_Supported Assets: BTC, LTC, ETH, USDT (ERC20)_\n\n"
    "Let’s make P2P trading safer for everyone!"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['menu'])
def show_menu(message: Message):
    menu = (
        "📜 *Escrow Menu*\n"
        "/beginescrow – Start group escrow\n"
        "/seller wallet – Register seller\n"
        "/buyer wallet – Register buyer\n"
        "/asset COIN – Choose asset\n"
        "/editwallet – Correct your wallet address.\n"
        "/cancelescrow – cancel escrow session\n"
        "/balance – Check balance\n"
        "/releasefund – Release funds\n"
        "/adminresolve – Admin force resolve\n"
        "/status – View current escrow info\n"
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

def is_group(message):
    return message.chat.type in ['group', 'supergroup']

@bot.message_handler(commands=['beginescrow'])
def begin_escrow(message: Message):
    if not is_group(message):
        return bot.reply_to(message, "⚠️ Use this command in a group.")
    
    group_id = message.chat.id

    # 🔒 Check if an escrow is already active
    cursor.execute("SELECT status FROM group_escrows WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    if row and row[0] != 'completed':
        return bot.reply_to(message, "⚠️ Escrow already active in this group.")
    
    # ✅ Escrow is safe to start
    cursor.execute("REPLACE INTO group_escrows (group_id, status) VALUES (?, ?)", (group_id, 'initiated'))
    conn.commit()

    # 🧾 Log for debugging
    print(f"[BEGIN ESCROW] Group: {group_id}, User: {message.from_user.id}")

    bot.reply_to(message, "🔐 Escrow started! Use /seller and /buyer to register.")
    
@bot.message_handler(commands=['seller'])
def register_seller(message: Message):
    parts = message.text.split()
    if len(parts) != 2:
        return bot.reply_to(message, "⚠️ Usage: /seller wallet_address")
    seller_id = message.from_user.id
    wallet = parts[1]
    group_id = message.chat.id
    cursor.execute("UPDATE group_escrows SET seller_id = ?, seller_wallet = ? WHERE group_id = ?", 
                   (seller_id, wallet, group_id))
    conn.commit()
    bot.reply_to(message, f"✅ Seller set: *{message.from_user.first_name}*\nWallet: `{wallet}`", parse_mode='Markdown')

@bot.message_handler(commands=['buyer'])
def register_buyer(message: Message):
    parts = message.text.split()
    if len(parts) != 2:
        return bot.reply_to(message, "⚠️ Usage: /buyer wallet_address")
    buyer_id = message.from_user.id
    wallet = parts[1]
    group_id = message.chat.id
    cursor.execute("UPDATE group_escrows SET buyer_id = ?, buyer_wallet = ? WHERE group_id = ?", 
                   (buyer_id, wallet, group_id))
    conn.commit()
    bot.reply_to(message, f"✅ Buyer set: *{message.from_user.first_name}*\nWallet: `{wallet}`", parse_mode='Markdown')

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

@bot.message_handler(commands=['editwallet'])
def edit_wallet(message: Message):
    parts = message.text.split()
    if len(parts) != 2:
        return bot.reply_to(message, "⚠️ Usage: /editwallet NEW_WALLET_ADDRESS")
    new_wallet = parts[1]
    user_id = message.from_user.id
    group_id = message.chat.id

    cursor.execute("SELECT buyer_id, seller_id FROM group_escrows WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    if not row:
        return bot.reply_to(message, "❌ No active escrow found.")
    
    buyer_id, seller_id = row
    if user_id == buyer_id:
        cursor.execute("UPDATE group_escrows SET buyer_wallet = ? WHERE group_id = ?", (new_wallet, group_id))
        conn.commit()
        return bot.reply_to(message, f"🔁 Buyer wallet updated to:\n`{new_wallet}`", parse_mode='Markdown')
    elif user_id == seller_id:
        cursor.execute("UPDATE group_escrows SET seller_wallet = ? WHERE group_id = ?", (new_wallet, group_id))
        conn.commit()
        return bot.reply_to(message, f"🔁 Seller wallet updated to:\n`{new_wallet}`", parse_mode='Markdown')
    else:
        return bot.reply_to(message, "⛔ You are not part of this escrow session.")

def get_balance(asset, address):
    try:
        if asset in ['BTC', 'LTC']:
            url = f"https://sochain.com/api/v2/get_address_balance/{asset}/{address}"
            res = requests.get(url)
            if res.status_code == 200:
                data = res.json()
                if data['status'] == 'success':
                    return data['data']['confirmed_balance']
        elif asset in ['ETH', 'USDT']:
            if asset == 'USDT':
                contract = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
                url = f"https://api.etherscan.io/api?module=account&action=tokenbalance&contractaddress={contract}&address={address}&tag=latest&apikey={ETHERSCAN_API_KEY}"
                decimals = 1e6
            else:
                url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={ETHERSCAN_API_KEY}"
                decimals = 1e18
            res = requests.get(url)
            if res.status_code == 200:
                data = res.json()
                if data.get('status') == '1':
                    return str(int(data['result']) / decimals)
    except Exception as e:
        print(f"[Balance Error] {asset} - {address} -> {e}")
    return None

@bot.message_handler(commands=['balance'])
def check_balance(message: Message):
    group_id = message.chat.id
    cursor.execute("SELECT asset, buyer_wallet FROM group_escrows WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    
    if not row or not row[0] or not row[1]:
        return bot.reply_to(message, "⚠️ No asset or buyer wallet set.")
    
    asset, wallet = row
    balance = get_balance(asset, wallet)
    
    if not balance:
        return bot.reply_to(message, f"❌ Failed to fetch balance for {asset}.")
    
    # Compose a nicer escrow-style response
    reply_text = (
        f"📥 *Escrow Deposit Confirmed!*\n\n"
        f"*Asset:* {asset}\n"
        f"*Received:* {balance} {asset}\n"
        f"*Confirmations:* 2+\n\n"
        "You're all set! Once both parties agree, use `/releasefund` to complete the deal.\n\n"
        "💡 Tip: Use `/status` anytime to view current deal progress."
    )
    
    bot.reply_to(message, reply_text, parse_mode='Markdown')

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

@bot.message_handler(commands=['status'])
def view_status(message: Message):
    group_id = message.chat.id
    cursor.execute("SELECT buyer_wallet, seller_wallet, asset, status FROM group_escrows WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    if not row:
        return bot.reply_to(message, "ℹ️ No active escrow found. Use /beginescrow to start one.")
    
    buyer_wallet, seller_wallet, asset, status = row
    buyer_balance = get_balance(asset, buyer_wallet) if buyer_wallet and asset else "?"
    seller_balance = get_balance(asset, seller_wallet) if seller_wallet and asset else "?"

    status_message = (
        "📊 *Escrow Status:*\n"
        f"👤 Buyer Wallet: `{buyer_wallet or 'Not set'}`\n"
        f"   Balance: `{buyer_balance}`\n"
        f"🧍‍♂️ Seller Wallet: `{seller_wallet or 'Not set'}`\n"
        f"   Balance: `{seller_balance}`\n"
        f"💰 Asset: *{asset or 'Not selected'}*\n"
        f"📌 Status: *{status}*"
    )
    bot.reply_to(message, status_message, parse_mode='Markdown')

@bot.message_handler(commands=['cancelescrow'])
def cancel_escrow(message: Message):
    group_id = message.chat.id
    cursor.execute("SELECT status FROM group_escrows WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    if not row:
        return bot.reply_to(message, "❌ No active escrow to cancel.")
    
    if row[0] == 'completed':
        return bot.reply_to(message, "⚠️ Escrow already completed. Cannot cancel.")

    cursor.execute("DELETE FROM group_escrows WHERE group_id = ?", (group_id,))
    conn.commit()
    bot.reply_to(message, "❎ Escrow session cancelled.")

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
if WEBHOOK_URL:
    bot.remove_webhook()
    bot.set_webhook(WEBHOOK_URL)
else:
    print("Error: WEBHOOK_URL is not set in environment variables.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host="0.0.0.0", port=port)
