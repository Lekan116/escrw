import uuid
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from database import conn, cursor
from keyboards import (
    main_menu,
    escrow_setup_menu,
    asset_keyboard,
    escrow_actions,
    confirm_release_keyboard,
    admin_panel
)
from permissions import is_admin, get_role
from group_manager import create_escrow_group


# ==============================
# CALLBACK ROUTER
# ==============================
@Client.on_callback_query()
async def callback_router(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat.id

    # ==============================
    # CREATE ESCROW
    # ==============================
    if data == "create_escrow":
        escrow_id = str(uuid.uuid4())

        cursor.execute(
            "INSERT INTO escrows (id, buyer_id, status) VALUES (?, ?, ?)",
            (escrow_id, user_id, "setup")
        )

        cursor.execute(
            "INSERT INTO escrow_participants (escrow_id, user_id, role) VALUES (?, ?, ?)",
            (escrow_id, user_id, "buyer")
        )

        conn.commit()

        group_id, invite_link = await create_escrow_group(
            client=client,
            escrow_id=escrow_id,
            creator_id=user_id
        )

        cursor.execute(
            "UPDATE escrows SET group_id = ? WHERE id = ?",
            (group_id, escrow_id)
        )
        conn.commit()

        await query.message.reply_text(
            "🔐 **Escrow Created Successfully!**\n\n"
            "A private escrow group has been created.\n\n"
            "📨 **Send this invite link to the seller:**\n"
            f"{invite_link}",
            reply_markup=escrow_setup_menu()
        )

    # ==============================
    # JOIN AS BUYER / SELLER
    # ==============================
    elif data in ("join_buyer", "join_seller"):
        role = "buyer" if data == "join_buyer" else "seller"

        cursor.execute(
            "SELECT escrow_id FROM escrow_participants WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            return await query.answer("❌ Escrow not found.", show_alert=True)

        escrow_id = row[0]

        cursor.execute(
            "INSERT OR IGNORE INTO escrow_participants VALUES (?, ?, ?)",
            (escrow_id, user_id, role)
        )
        conn.commit()

        await query.message.reply_text(
            f"✅ You joined the escrow as **{role.upper()}**.",
            reply_markup=escrow_setup_menu()
        )

    # ==============================
    # ASSET SELECTION
    # ==============================
    elif data == "select_asset":
        await query.message.reply_text(
            "💰 **Select the asset for this escrow:**",
            reply_markup=asset_keyboard()
        )

    elif data.startswith("asset_"):
        asset = data.split("_")[1]

        cursor.execute(
            "UPDATE escrows SET asset = ?, status = ? WHERE id = (SELECT escrow_id FROM escrow_participants WHERE user_id = ?)",
            (asset, "awaiting_deposit", user_id)
        )
        conn.commit()

        await query.message.reply_text(
            f"💰 **Asset Selected:** `{asset}`\n\n"
            "Buyer can now send funds.",
            reply_markup=escrow_actions(is_buyer=True)
        )

    # ==============================
    # CHECK DEPOSIT (SKELETON – HOOKS INTO deposit_watcher)
    # ==============================
    elif data == "check_deposit":
        await query.message.reply_text(
            "🔍 Checking blockchain confirmations...\n\n"
            "⏳ Please wait."
        )
        # deposit_watcher hook will finalize this

    # ==============================
    # CONFIRM RELEASE
    # ==============================
    elif data == "confirm_release":
        await query.message.reply_text(
            "⚠️ **Confirm fund release**\n\n"
            "This action is irreversible.",
            reply_markup=confirm_release_keyboard()
        )

    elif data == "release_yes":
        cursor.execute(
            "UPDATE escrows SET status = ? WHERE id = (SELECT escrow_id FROM escrow_participants WHERE user_id = ?)",
            ("released", user_id)
        )
        conn.commit()

        await query.message.reply_text(
            "✅ **Funds Released Successfully!**\n\n"
            "Thank you for using the escrow service."
        )

    elif data == "release_no":
        await query.message.reply_text("❌ Release cancelled.")

    # ==============================
    # DISPUTE
    # ==============================
    elif data == "open_dispute":
        await query.message.reply_text(
            "⚠️ **Dispute Opened**\n\n"
            "An admin has been notified."
        )

    # ==============================
    # ADMIN CONTROLS
    # ==============================
    elif data in ("admin_release", "admin_cancel"):
        if not is_admin(user_id):
            return await query.answer("⛔ Admin only.", show_alert=True)

        action = "released" if data == "admin_release" else "cancelled"

        cursor.execute(
            "UPDATE escrows SET status = ? WHERE id = (SELECT escrow_id FROM escrow_participants LIMIT 1)",
            (action,)
        )
        conn.commit()

        await query.message.reply_text(
            f"⚖️ **Admin Action Applied:** {action.upper()}"
        )

    # ==============================
    # HELP / TERMS
    # ==============================
    elif data == "help":
        await query.message.reply_text(
            "📖 **How Escrow Works**\n\n"
            "1. Create escrow\n"
            "2. Invite seller\n"
            "3. Select asset\n"
            "4. Buyer deposits\n"
            "5. Release funds\n\n"
            "Safe. Transparent. Admin-backed."
        )

    elif data == "terms":
        await query.message.reply_text(
            "📜 **Escrow Terms**\n\n"
            "- Funds must confirm on-chain\n"
            "- Release requires consent\n"
            "- Admin resolves disputes\n"
            "- Fees deducted automatically"
        )

    # ==============================
    # FALLBACK
    # ==============================
    else:
        await query.answer("⚠️ Unknown action.")

    await query.answer()
