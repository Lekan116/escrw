import os
import sqlite3
import telebot
from dotenv import load_dotenv
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Load wallet addresses
ASSET_WALLETS = {
    'LTC': os.getenv('LTC_WALLET'),
    'BTC': os.getenv('BTC_WALLET'),
    'USDT': os.getenv('USDT_WALLET'),
}

# === DATABASE ===
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

# === START GROUP ESCROW ===
@bot.message_handler(commands=['beginescrow'])
def begin_escrow(message: Message):
    group_id = message.chat.id
    cursor.execute("REPLACE INTO group_escrows (group_id, status) VALUES (?, ?)", (group_id, 'initiated'))
    conn.commit()
    bot.reply_to(message, "🔐 Escrow session started!\nUse /seller and /buyer to register parties.")

# === REGISTER SELLER ===
@bot.message_handler(commands=['seller'])
def register_seller(message: Message):
    parts = message.text.split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /seller @username wallet_address")
    seller_id = message.from_user.id
    seller_wallet = parts[2]
    group_id = message.chat.id
    cursor.execute("UPDATE group_escrows SET seller_id = ?, seller_wallet = ? WHERE group_id = ?", (seller_id, seller_wallet, group_id))
    conn.commit()
    bot.reply_to(message, f"✅ Seller set: {parts[1]}\nWallet: `{seller_wallet}`", parse_mode='Markdown')

# === REGISTER BUYER ===
@bot.message_handler(commands=['buyer'])
def register_buyer(message: Message):
    parts = message.text.split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /buyer @username wallet_address")
    buyer_id = message.from_user.id
    buyer_wallet = parts[2]
    group_id = message.chat.id
    cursor.execute("UPDATE group_escrows SET buyer_id = ?, buyer_wallet = ? WHERE group_id = ?", (buyer_id, buyer_wallet, group_id))
    conn.commit()
    bot.reply_to(message, f"✅ Buyer set: {parts[1]}\nWallet: `{buyer_wallet}`", parse_mode='Markdown')

# === CHOOSE ASSET ===
@bot.message_handler(commands=['asset', 'choose'])
def choose_asset(message: Message):
    markup = InlineKeyboardMarkup()
    for asset in ASSET_WALLETS.keys():
        markup.add(InlineKeyboardButton(asset, callback_data=f"set_asset:{asset}"))
    bot.reply_to(message, "💠 Select an asset for escrow:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_asset:'))
def callback_set_asset(call):
    asset = call.data.split(':')[1]
    group_id = call.message.chat.id
    cursor.execute("UPDATE group_escrows SET asset = ? WHERE group_id = ?", (asset, group_id))
    conn.commit()
    bot.edit_message_text(
        f"💰 Asset selected: {asset}\n📥 Send funds to the escrow wallet:\n`{ASSET_WALLETS[asset]}`",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='Markdown'
    )

# === BALANCE CHECK ===
@bot.message_handler(commands=['balance'])
def check_balance(message: Message):
    group_id = message.chat.id
    cursor.execute("SELECT asset FROM group_escrows WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    if not row or not row[0]:
        return bot.reply_to(message, "⚠️ No asset selected yet. Use /asset to choose.")
    asset = row[0]
    bot.reply_to(message, f"🧾 Escrow is set for asset: *{asset}*\n🔎 Manual balance check pending...", parse_mode='Markdown')

# === RELEASE FUNDS ===
@bot.message_handler(commands=['releasefund'])
def release_funds(message: Message):
    group_id = message.chat.id
    cursor.execute("SELECT seller_wallet, asset FROM group_escrows WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    if not row:
        return bot.reply_to(message, "❌ No active escrow found.")
    seller_wallet, asset = row
    bot.reply_to(message, f"✅ Funds released to seller:\nWallet: `{seller_wallet}`\nAsset: *{asset}*", parse_mode='Markdown')

# === ADMIN FORCE RESOLVE ===
@bot.message_handler(commands=['adminresolve'])
def admin_force_release(message: Message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ Only admin can use this command.")
    group_id = message.chat.id
    cursor.execute("DELETE FROM group_escrows WHERE group_id = ?", (group_id,))
    conn.commit()
    bot.reply_to(message, "🛑 Escrow forcibly resolved by admin.")

# === RUN BOT ===
bot.infinity_polling()
