import os

def create_tables(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escrows (
            chat_id INTEGER PRIMARY KEY,
            confirmed_users TEXT,
            cancelled INTEGER DEFAULT 0
        )
    """)

def create_escrow(message, cursor, conn, bot):
    chat_id = message.chat.id
    cursor.execute("SELECT * FROM escrows WHERE chat_id = ?", (chat_id,))
    if cursor.fetchone():
        bot.send_message(chat_id, "⚠️ Escrow already active. Use /status.")
        return
    cursor.execute("INSERT INTO escrows (chat_id, confirmed_users, cancelled) VALUES (?, ?, ?)", (chat_id, "", 0))
    conn.commit()
    bot.send_message(chat_id, f"✅ Escrow initiated!\n{get_wallets()}", parse_mode='Markdown')

def confirm_escrow(message, cursor, conn, bot):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    cursor.execute("SELECT confirmed_users FROM escrows WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    if not row:
        bot.send_message(chat_id, "❌ No active escrow. Use /escrow.")
        return

    confirmed_users = row[0].split(",") if row[0] else []
    if user_id not in confirmed_users:
        confirmed_users.append(user_id)
        cursor.execute("UPDATE escrows SET confirmed_users = ? WHERE chat_id = ?", (",".join(confirmed_users), chat_id))
        conn.commit()

    if len(confirmed_users) >= 2:
        bot.send_message(chat_id, "✅ Both parties confirmed. Funds can be released.")
    else:
        bot.send_message(chat_id, "☑️ Confirmation received. Waiting for the other party.")

def cancel_escrow(message, cursor, conn, bot):
    chat_id = message.chat.id
    cursor.execute("SELECT * FROM escrows WHERE chat_id = ?", (chat_id,))
    if not cursor.fetchone():
        bot.send_message(chat_id, "❌ No active escrow.")
        return
    cursor.execute("UPDATE escrows SET cancelled = 1 WHERE chat_id = ?", (chat_id,))
    conn.commit()
    bot.send_message(chat_id, "❌ Escrow cancelled.")

def get_status(message, cursor, bot):
    chat_id = message.chat.id
    cursor.execute("SELECT confirmed_users, cancelled FROM escrows WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    if not row:
        bot.send_message(chat_id, "ℹ️ No active escrow.")
        return

    confirmed = len(row[0].split(",")) if row[0] else 0
    cancelled = bool(row[1])
    bot.send_message(chat_id, f"""
🔒 *Escrow Status*:
- Confirmations: {confirmed}/2
- Cancelled: {'✅' if cancelled else '❌'}
""", parse_mode='Markdown')

def get_wallets():
    return f"""
💼 *Send crypto to hold in escrow:*
- BTC: `{os.getenv("BTC_ADDRESS")}`
- LTC: `{os.getenv("LTC_ADDRESS")}`
- ETH: `{os.getenv("ETH_ADDRESS")}`
- USDT: `{os.getenv("USDT_ADDRESS")}`
"""

def verify_wallet(message, bot):
    bot.send_message(message.chat.id, get_wallets(), parse_mode='Markdown')
