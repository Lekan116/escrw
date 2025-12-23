import uuid
from pyrogram import Client, filters
from database import cursor, conn
from keyboards import main_menu
from permissions import is_admin
from group_manager import create_escrow_group

@Client.on_callback_query()
async def callback_router(client, query):
    data = query.data
    user_id = query.from_user.id

    if data == "create_escrow":
        escrow_id = str(uuid.uuid4())

        # Insert escrow record
        cursor.execute(
            """
            INSERT INTO escrows (id, buyer_id, status)
            VALUES (?, ?, 'awaiting_seller')
            """,
            (escrow_id, user_id)
        )

        # Insert escrow participant as buyer
        cursor.execute(
            """
            INSERT INTO escrow_participants (escrow_id, user_id, role)
            VALUES (?, ?, 'buyer')
            """,
            (escrow_id, user_id)
        )

        conn.commit()

        # Create a private group for the escrow
        group_id, invite_link = await create_escrow_group(
            client,
            escrow_id,
            user_id
        )

        await query.message.reply_text(
            "Escrow created.\n\n"
            "A private group has been created.\n"
            "Send this invite link to the seller:\n\n"
            f"{invite_link}"
        )

    elif data == "help":
        await query.message.reply_text(
            "How escrow works:\n"
            "1. Create escrow\n"
            "2. Seller joins via link\n"
            "3. Buyer deposits funds\n"
            "4. Bot confirms deposit\n"
            "5. Delivery\n"
            "6. Release"
        )

    elif data == "terms":
        await query.message.reply_text(
            "Escrow rules:\n"
            "- Funds must be confirmed on-chain\n"
            "- Release requires both parties\n"
            "- Admin resolves disputes\n"
            "- Fees are deducted automatically"
        )

    await query.answer()
