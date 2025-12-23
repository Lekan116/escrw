import os
import asyncio
import uuid
from dotenv import load_dotenv

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import conn, cursor
from utils import calculate_fee
from deposit_watcher import deposit_watcher
from keyboards import start_keyboard, escrow_actions
from group_manager import create_escrow_group

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Client(
    "escrowbot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

# -------------------------------------------------
# START
# -------------------------------------------------

@app.on_message(filters.private & filters.command("start"))
async def start_handler(client, message):
    await message.reply(
        "P2P Escrow Bot\n\n"
        "This bot creates a private escrow group automatically.\n\n"
        "Flow:\n"
        "1. Buyer creates escrow\n"
        "2. Bot creates private group\n"
        "3. Buyer sends invite to seller\n"
        "4. Buyer deposits funds\n"
        "5. Deposit is auto-confirmed\n"
        "6. Seller delivers\n"
        "7. Both confirm release\n\n"
        "All actions use buttons.",
        reply_markup=start_keyboard()
    )

# -------------------------------------------------
# CREATE ESCROW (AUTO GROUP)
# -------------------------------------------------

@app.on_callback_query(filters.regex("^create_escrow$"))
async def create_escrow_cb(client, cb):
    escrow_id = str(uuid.uuid4())

    # Create escrow record
    cursor.execute(
        """
        INSERT INTO escrows (id, buyer_id, status)
        VALUES (?, ?, 'awaiting_seller')
        """,
        (escrow_id, cb.from_user.id)
    )

    cursor.execute(
        """
        INSERT INTO escrow_participants VALUES (?, ?, 'buyer')
        """,
        (escrow_id, cb.from_user.id)
    )
    conn.commit()

    # Create private group
    group_id, invite_link = await create_escrow_group(
        client,
        escrow_id,
        cb.from_user.id
    )

    await cb.message.reply(
        "Escrow created.\n\n"
        "A private escrow group has been created.\n\n"
        "Send this invite link to the seller:\n\n"
        f"{invite_link}"
    )

    await cb.answer()

# -------------------------------------------------
# SELLER JOIN DETECTION
# -------------------------------------------------

@app.on_message(filters.new_chat_members)
async def seller_join_handler(client, message):
    chat_id = message.chat.id

    cursor.execute(
        "SELECT id FROM escrows WHERE group_id = ? AND status = 'awaiting_seller'",
        (chat_id,)
    )
    row = cursor.fetchone()
    if not row:
        return

    escrow_id = row[0]

    for user in message.new_chat_members:
        cursor.execute(
            "INSERT OR IGNORE INTO escrow_participants VALUES (?, ?, 'seller')",
            (escrow_id, user.id)
        )
        cursor.execute(
            """
            UPDATE escrows
            SET seller_id = ?, status = 'awaiting_amount'
            WHERE id = ?
            """,
            (user.id, escrow_id)
        )
        conn.commit()

        await message.reply(
            "Seller joined.\n\n"
            "Buyer must now set asset and amount."
        )

# -------------------------------------------------
# SET ASSET
# -------------------------------------------------

@app.on_callback_query(filters.regex("^asset_"))
async def set_asset_cb(client, cb):
    asset = cb.data.split("_")[1]

    cursor.execute(
        "UPDATE escrows SET asset = ? WHERE group_id = ?",
        (asset, cb.message.chat.id)
    )
    conn.commit()

    await cb.message.reply("Asset set. Now enter the amount.")
    await cb.answer()

# -------------------------------------------------
# SET AMOUNT
# -------------------------------------------------

@app.on_message(filters.group & filters.text)
async def amount_input(client, message):
    cursor.execute(
        "SELECT status FROM escrows WHERE group_id = ?",
        (message.chat.id,)
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
    conn.commit()

    await message.reply(
        f"Amount locked.\n\n"
        f"Amount: {amount}\n"
        f"Fee: {fee}\n"
        f"Seller receives: {net}\n\n"
        "Waiting for deposit."
    )

# -------------------------------------------------
# RELEASE (DUAL CONFIRM)
# -------------------------------------------------

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
        await cb.message.reply("Escrow completed. Funds released.")
    else:
        await cb.answer("Confirmation recorded")

# -------------------------------------------------
# BACKGROUND TASKS + RUN
# -------------------------------------------------

async def main():
    async with app:
        app.loop.create_task(deposit_watcher(app))
        await asyncio.Event().wait()

app.run(main())
