import os

# === CREATE TABLE IF NOT EXISTS ===
def create_tables(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escrows (
            chat_id INTEGER PRIMARY KEY,
            confirmed_users TEXT,
            cancelled INTEGER DEFAULT 0
        )
    """)

# === START ESCROW ===
def create_escrow(message, cursor, conn, bot):
    chat_id = message.chat.id
    cursor.execute("SELECT * FROM escrows WHERE chat_id = ?", (chat_id,))
    if cursor.fetchone():
        return bot.send_message(chat_id, "⚠️ You already have an active escrow. Use /status to view it.")

    cursor.execute(
        "INSERT INTO escrows (chat_id, confirmed_users, cancelled) VALUES (?, ?, ?)",
        (chat_id, "", 0)
    )
    conn.commit()
    bot.send_message(chat_id, f"✅ Escrow started!\n{get_wallets()}", parse_mode='Markdown')

# === CONFIRM ESCROW ===
def confirm_escrow(message, cursor, conn, bot):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)

    cursor.execute("SELECT confirmed_users FROM escrows WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()

    if not row:
        return bot.send_message(chat_id, "❌ No active escrow. Use /escrow to start one.")

    confirmed_users = row[0].split(",") if row[0] else []
    
    if user_id not in confirmed_users:
        confirmed_users.append(user_id)
        cursor.execute(
            "UPDATE escrows SET confirmed_users = ? WHERE chat_id = ?",
            (",".join(confirmed_users), chat_id)
        )
        conn.commit()

    if len(confirmed_users) >= 2:
        bot.send_message(chat_id, "✅ Both users confirmed! Escrow complete. Funds can now be released.")
    else:
        bot.send_message(chat_id, "☑️ Your confirmation is recorded. Waiting for the second party...")

# === CANCEL ESCROW ===
def cancel_escrow(message, cursor, conn, bot):
    chat_id = message.chat.id

    cursor.execute("SELECT * FROM escrows WHERE chat_id = ?", (chat_id,))
    if not cursor.fetchone():
        return bot.send_message(chat_id, "❌ No active escrow to cancel.")

    cursor.execute("UPDATE escrows SET cancelled = 1 WHERE chat_id = ?", (chat_id,))
    conn.commit()
    bot.send_message(chat_id, "❌ Escrow has been cancelled.")

# === ESCROW STATUS ===
def get_status(message, cursor, bot):
    chat_id = message.chat.id

    cursor.execute("SELECT confirmed_users, cancelled FROM escrows WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()

    if not row:
        return bot.send_message(chat_id, "ℹ️ You have no active escrow.")

    confirmed = len(row[0].split(",")) if row[0] else 0
    cancelled = bool(row[1])

    bot.send_message(message.chat.id, f"""
🔒 *Escrow Status*:
- Confirmations: {confirmed}/2
- Cancelled: {'✅ Yes' if cancelled else '❌ No'}
""", parse_mode='Markdown')

# === WALLET DISPLAY ===
def get_wallets():
    return f"""
💼 *Send Crypto to Escrow*:
₿ *BTC*: `{os.getenv("BTC_ADDRESS")}`
Ł *LTC*: `{os.getenv("LTC_ADDRESS")}`
Ξ *ETH*: `{os.getenv("ETH_ADDRESS")}`
💲 *USDT*: `{os.getenv("USDT_ADDRESS")}`
"""

# === SHOW WALLETS ===
def verify_wallet(message, bot):
    bot.send_message(message.chat.id, get_wallets(), parse_mode='Markdown')
