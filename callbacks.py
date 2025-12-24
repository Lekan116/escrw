import uuid
from pyrogram import filters
from pyrogram.types import CallbackQuery

from database import cursor, conn
from keyboards import (
    start_keyboard,
    escrow_setup_keyboard,
    asset_keyboard,
    escrow_action_keyboard,
    confirm_release_keyboard
)
from permissions import get_role, is_admin
from group_manager import create_escrow_group
from utils import calculate_fee, confirm_deposit


# ==============================
# START
# ==============================
async def start_callback(client, cq: CallbackQuery):
    await cq.message.edit_text(
        "🔐 Welcome to Escrow Bot\n\n"
        "Safe P2P trading with auto-hold & dispute protection.",
        reply_markup=start_keyboard()
    )


# ==============================
# CREATE ESCROW
# ==============================
async def create_escrow(client, cq: CallbackQuery):
    escrow_id = str(uuid.uuid4())

    cursor.execute(
        """
        INSERT INTO escrows (
            id, buyer_id, status
        ) VALUES (?, ?, 'setup')
        """,
        (escrow_id, cq.from_user.id)
    )
    conn.commit()

    group_id, invite = await create_escrow_group(
        client,
        escrow_id,
        cq.from_user.id
    )

    await cq.message.edit_text(
        f"🆕 Escrow Created\n\n"
        f"Escrow ID: `{escrow_id[:8]}`\n\n"
        f"Invite the other party:\n{invite}",
        reply_markup=escrow_setup_keyboard()
    )


# ==============================
# ASSET SELECTION
# ==============================
async def select_asset(client, cq: CallbackQuery):
    await cq.message.edit_text(
        "💰 Select the asset for this escrow:",
        reply_markup=asset_keyboard()
    )


async def set_asset(client, cq: CallbackQuery):
    asset = cq.data.split(":")[1]

    cursor.execute(
        "UPDATE escrows SET asset = ? WHERE buyer_id = ? AND status = 'setup'",
        (asset, cq.from_user.id)
    )
    conn.commit()

    await cq.answer(f"{asset} selected")


# ==============================
# CHECK DEPOSIT
# ==============================
async def check_deposit(client, cq: CallbackQuery):
    cursor.execute(
        """
        SELECT id, group_id FROM escrows
        WHERE buyer_id = ? AND status = 'awaiting_deposit'
        """,
        (cq.from_user.id,)
    )
    row = cursor.fetchone()
    if not row:
        return await cq.answer("No pending escrow", show_alert=True)

    escrow_id, group_id = row

    if confirm_deposit(escrow_id, cq.from_user.id):
        await client.send_message(
            group_id,
            "✅ Deposit confirmed.\nSeller may deliver."
        )


# ==============================
# RELEASE FLOW
# ==============================
async def confirm_release(client, cq: CallbackQuery):
    await cq.message.reply(
        "⚠️ Confirm fund release?",
        reply_markup=confirm_release_keyboard()
    )


async def release_yes(client, cq: CallbackQuery):
    cursor.execute(
        """
        UPDATE escrows
        SET status = 'completed'
        WHERE group_id = ?
        """,
        (cq.message.chat.id,)
    )
    conn.commit()

    await cq.message.edit_text("✅ Escrow completed. Funds released.")


async def release_no(client, cq: CallbackQuery):
    await cq.answer("Release cancelled")
