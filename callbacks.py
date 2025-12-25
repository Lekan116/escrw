import uuid
from pyrogram.types import CallbackQuery
from database import cursor, conn
from keyboards import start_keyboard, asset_keyboard
from group_manager import create_escrow_group
from utils import escrow_terms, help_text, ASSET_WALLETS


async def start_callback(client, message):
    await message.reply_text(
        "👋 *Welcome to P2P EscrowBot*\n\n"
        "Secure escrow for safe trading.\n"
        "No trust required.",
        reply_markup=start_keyboard()
    )


async def create_escrow(client, cq: CallbackQuery):
    buyer_id = cq.from_user.id
    escrow_id = str(uuid.uuid4())

    cursor.execute(
        "INSERT INTO escrows VALUES (?, ?, ?, ?, ?, ?)",
        (escrow_id, buyer_id, None, None, None, "awaiting_seller")
    )

    cursor.execute(
        "INSERT INTO participants VALUES (?, ?, ?)",
        (escrow_id, buyer_id, "buyer")
    )

    conn.commit()

    _, invite = await create_escrow_group(client, escrow_id)

    await cq.message.reply_text(
        "✅ *Escrow Created*\n\n"
        "📩 Send this invite link to the seller:\n\n"
        f"{invite}"
    )


async def select_asset(client, cq: CallbackQuery):
    await cq.message.reply_text(
        "💰 Select the asset for this deal:",
        reply_markup=asset_keyboard()
    )


async def set_asset(client, cq: CallbackQuery):
    asset = cq.data.split(":")[1]
    wallet = ASSET_WALLETS.get(asset)

    await cq.message.reply_text(
        f"✅ *Asset Selected: {asset}*\n\n"
        f"📥 Buyer must send funds to:\n"
        f"`{wallet}`\n\n"
        "⚠️ Send exact asset only."
    )


async def show_terms(client, cq: CallbackQuery):
    await cq.message.reply_text(escrow_terms())


async def show_help(client, cq: CallbackQuery):
    await cq.message.reply_text(help_text())
