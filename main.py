import os
import asyncio
from dotenv import load_dotenv
from deposit_watcher import deposit_watcher
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatMemberUpdated
)

from database import conn, cursor
from utils import calculate_fee
from keyboards import (
    start_keyboard,
    escrow_panel,
    asset_keyboard,
    confirm_release_keyboard
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
BOT_USERNAME = os.getenv("BOT_USERNAME")

app = Client(
    "escrowbot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

# ---------------------------
# START / DEEP LINK HANDLER
# ---------------------------

@app.on_message(filters.private & filters.command("start"))
async def start_handler(client, message):
    if len(message.command) > 1 and message.command[1].startswith("escrow_"):
        escrow_id = message.command[1].split("_")[1]

        cursor.execute(
            "SELECT buyer_id, seller_id, status FROM escrows WHERE id = ?",
            (escrow_id,)
        )
        row = cursor.fetchone()

        if not row:
            return await message.reply("Invalid or expired escrow link.")

        buyer_id, seller_id, status = row

        if message.from_user.id == buyer_id:
            return await message.reply("You are already registered as the buyer.")

        if seller_id:
            return await message.reply("Seller already registered for this escrow.")

        cursor.execute(
            "UPDATE escrows SET seller_id = ?, status = ? WHERE id = ?",
            (message.from_user.id, "participants_set", escrow_id)
        )
        conn.commit()

        await message.reply(
            "You are now registered as the seller.\n\n"
            "Create a group, add this bot, and the escrow will activate automatically."
        )
        return

    await message.reply(
        "Welcome to P2P Escrow Bot\n\n"
        "This bot helps two parties complete trades safely using a neutral escrow process.\n\n"
        "How it works:\n"
        "1. Buyer creates escrow\n"
        "2. Bot generates a secure invite link\n"
        "3. Buyer sends the link to the seller\n"
        "4. Seller joins using the link\n"
        "5. Escrow room is activated\n"
        "6. Buyer sends funds\n"
        "7. Seller delivers\n"
        "8. Both parties confirm release\n\n"
        "The bot does not hold funds.\n"
        "All actions are performed using buttons.\n",
        reply_markup=start_keyboard()
    )

# ---------------------------
# CREATE ESCROW
# ---------------------------

@app.on_callback_query(filters.regex("^create_escrow$"))
async def create_escrow_cb(client, cb):
    import uuid

    escrow_id = str(uuid.uuid4())[:8]

    cursor.execute(
        """
        INSERT INTO escrows (id, buyer_id, status)
        VALUES (?, ?, ?)
        """,
        (escrow_id, cb.from_user.id, "waiting_seller")
    )
    conn.commit()

    link = f"https://t.me/{BOT_USERNAME}?start=escrow_{escrow_id}"

    await cb.message.reply(
        f"Escrow created.\n\n"
        f"Escrow ID: `{escrow_id}`\n\n"
        f"Send this link to the seller:\n{link}",
        parse_mode="markdown"
    )

# ---------------------------
# GROUP BINDING (BOT ADDED)
# ---------------------------

@app.on_message(filters.group & filters.new_chat_members)
async def on_bot_added(client, message):
    if client.me.id not in [u.id for u in message.new_chat_members]:
        return

    cursor.execute(
        """
        SELECT id FROM escrows
        WHERE status = 'participants_set'
        ORDER BY created_at DESC
        LIMIT 1
        """
    )
    row = cursor.fetchone()

    if not row:
        return await message.reply("No pending escrow found.")

    escrow_id = row[0]

    cursor.execute(
        """
        UPDATE escrows
        SET group_id = ?, status = 'active'
        WHERE id = ?
        """,
        (message.chat.id, escrow_id)
    )
    conn.commit()

    await message.reply(
        "Escrow room activated.\n\n"
        "Use the control panel below to proceed.",
        reply_markup=escrow_panel()
    )

# ---------------------------
# ASSET SELECTION
# ---------------------------

@app.on_callback_query(filters.regex("^set_asset$"))
async def set_asset_cb(client, cb):
    await cb.message.reply(
        "Select the asset for this escrow:",
        reply_markup=asset_keyboard()
    )

@app.on_callback_query(filters.regex("^asset_"))
async def asset_selected_cb(client, cb):
    asset = cb.data.split("_")[1]

    cursor.execute(
        "UPDATE escrows SET asset = ? WHERE group_id = ?",
        (asset, cb.message.chat.id)
    )
    conn.commit()

    await cb.answer(f"{asset} selected")

# ---------------------------
# SET AMOUNT
# ---------------------------

@app.on_callback_query(filters.regex("^set_amount$"))
async def ask_amount_cb(client, cb):
    cursor.execute(
        "UPDATE sessions SET state = 'awaiting_amount' WHERE user_id = ?",
        (cb.from_user.id,)
    )
    conn.commit()

    await cb.message.reply("Enter the escrow amount:")

@app.on_message(filters.group & filters.text)
async def amount_input(client, message):
    cursor.execute(
        "SELECT state FROM sessions WHERE user_id = ?",
        (message.from_user.id,)
    )
    row = cursor.fetchone()

    if not row or row[0] != "awaiting_amount":
        return

    try:
        amount = float(message.text)
    except ValueError:
        return await message.reply("Invalid amount.")

    fee, net = calculate_fee(amount)

    cursor.execute(
        """
        UPDATE escrows
        SET amount = ?, fee = ?, net_amount = ?, status = 'awaiting_deposit'
        WHERE group_id = ?
        """,
        (amount, fee, net, message.chat.id)
    )

    cursor.execute(
        "DELETE FROM sessions WHERE user_id = ?",
        (message.from_user.id,)
    )

    conn.commit()

    await message.reply(
        f"Amount locked.\n\n"
        f"Amount: {amount}\n"
        f"Fee: {fee}\n"
        f"Seller receives: {net}",
        reply_markup=escrow_panel()
    )

# ---------------------------
# STATUS
# ---------------------------

@app.on_callback_query(filters.regex("^status$"))
async def status_cb(client, cb):
    cursor.execute(
        """
        SELECT asset, amount, fee, net_amount, status
        FROM escrows WHERE group_id = ?
        """,
        (cb.message.chat.id,)
    )
    row = cursor.fetchone()

    if not row:
        return await cb.message.reply("No active escrow.")

    asset, amount, fee, net, status = row

    await cb.message.reply(
        f"Escrow Status\n\n"
        f"Asset: {asset}\n"
        f"Amount: {amount}\n"
        f"Fee: {fee}\n"
        f"Seller Receives: {net}\n"
        f"State: {status}"
    )

# ---------------------------
# RELEASE FLOW
# ---------------------------

@app.on_callback_query(filters.regex("^release$"))
async def release_cb(client, cb):
    await cb.message.reply(
        "Both parties must confirm release.",
        reply_markup=confirm_release_keyboard()
    )

@app.on_callback_query(filters.regex("^confirm_release$"))
async def confirm_release_cb(client, cb):
    cursor.execute(
        """
        SELECT buyer_id, seller_id, buyer_confirmed, seller_confirmed
        FROM escrows WHERE group_id = ?
        """,
        (cb.message.chat.id,)
    )
    row = cursor.fetchone()

    if not row:
        return

    buyer_id, seller_id, b_conf, s_conf = row

    if cb.from_user.id == buyer_id:
        b_conf = 1
    elif cb.from_user.id == seller_id:
        s_conf = 1
    else:
        return await cb.answer("Not authorized")

    cursor.execute(
        """
        UPDATE escrows
        SET buyer_confirmed = ?, seller_confirmed = ?
        WHERE group_id = ?
        """,
        (b_conf, s_conf, cb.message.chat.id)
    )
    conn.commit()

    if b_conf and s_conf:
        cursor.execute(
            "UPDATE escrows SET status = 'released' WHERE group_id = ?",
            (cb.message.chat.id,)
        )
        conn.commit()

        await cb.message.reply("Funds released. Escrow completed.")
    else:
        await cb.answer("Confirmation recorded")

# ---------------------------
# DISPUTE
# ---------------------------

@app.on_callback_query(filters.regex("^dispute$"))
async def dispute_cb(client, cb):
    link = await client.export_chat_invite_link(cb.message.chat.id)

    await client.send_message(
        ADMIN_ID,
        f"DISPUTE OPENED\n\nJoin escrow group:\n{link}"
    )

    cursor.execute(
        "UPDATE escrows SET status = 'disputed' WHERE group_id = ?",
        (cb.message.chat.id,)
    )
    conn.commit()

    await cb.message.reply("Dispute opened. Admin notified.")

# ---------------------------
# CANCEL
# ---------------------------

@app.on_callback_query(filters.regex("^cancel$"))
async def cancel_cb(client, cb):
    cursor.execute(
        "UPDATE escrows SET status = 'cancelled' WHERE group_id = ?",
        (cb.message.chat.id,)
    )
    conn.commit()

    await cb.message.reply("Escrow cancelled.")

# ---------------------------
# RUN
# ---------------------------

app.run()
