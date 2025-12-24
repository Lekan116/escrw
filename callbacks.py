import uuid
from pyrogram import filters
from database import cursor, conn
from keyboards import start_keyboard, escrow_keyboard, asset_keyboard
from permissions import get_role
from utils import validate_address

def register_callbacks(app):

    # =====================
    # CREATE ESCROW
    # =====================
    @app.on_callback_query(filters.regex("^create_escrow$"))
    async def create_escrow(client, cb):
        escrow_id = str(uuid.uuid4())[:8]

        cursor.execute("""
            INSERT INTO escrows (id, buyer_id, status)
            VALUES (?, ?, 'awaiting_group')
        """, (escrow_id, cb.from_user.id))
        conn.commit()

        await cb.message.reply(
            f"🆕 **Escrow Created**\n\n"
            f"🆔 Escrow ID: `{escrow_id}`\n\n"
            "📌 Steps:\n"
            "1️⃣ Create a group\n"
            "2️⃣ Add this bot\n"
            "3️⃣ Send inside group:\n\n"
            f"`/bind {escrow_id}`",
            parse_mode="Markdown"
        )
        await cb.answer()

    # =====================
    # ASSET SELECT
    # =====================
    @app.on_callback_query(filters.regex("^select_asset$"))
    async def select_asset(client, cb):
        await cb.message.reply("Choose asset:", reply_markup=asset_keyboard())
        await cb.answer()

    @app.on_callback_query(filters.regex("^asset_"))
    async def asset_chosen(client, cb):
        asset = cb.data.split("_")[1]

        cursor.execute(
            "UPDATE escrows SET asset=?, status='awaiting_deposit' WHERE group_id=?",
            (asset, cb.message.chat.id)
        )
        conn.commit()

        await cb.message.reply(f"💰 Asset selected: {asset}\nWaiting for deposit.")
        await cb.answer()

    # =====================
    # WALLET SET
    # =====================
    @app.on_callback_query(filters.regex("^set_buyer_wallet$"))
    async def buyer_wallet(client, cb):
        cursor.execute(
            "INSERT OR REPLACE INTO sessions VALUES (?, NULL, 'awaiting_buyer_wallet', CURRENT_TIMESTAMP)",
            (cb.from_user.id,)
        )
        conn.commit()
        await cb.message.reply("Send your wallet address:")
        await cb.answer()

    @app.on_callback_query(filters.regex("^set_seller_wallet$"))
    async def seller_wallet(client, cb):
        cursor.execute(
            "INSERT OR REPLACE INTO sessions VALUES (?, NULL, 'awaiting_seller_wallet', CURRENT_TIMESTAMP)",
            (cb.from_user.id,)
        )
        conn.commit()
        await cb.message.reply("Send your wallet address:")
        await cb.answer()
