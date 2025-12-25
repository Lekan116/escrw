from pyrogram import Client
from database import cursor, conn


async def create_escrow_group(app: Client, escrow_id: str):
    chat = await app.create_supergroup(
        title=f"P2P Escrow #{escrow_id[:6]}",
        description=(
            "🔒 Private Escrow Group\n\n"
            "• Buyer funds first\n"
            "• Seller delivers after confirmation\n"
            "• Funds released only by agreement\n"
            "• Admin resolves disputes if needed"
        )
    )

    invite = await app.create_chat_invite_link(chat.id, member_limit=2)

    cursor.execute(
        "UPDATE escrows SET group_id = ? WHERE id = ?",
        (chat.id, escrow_id)
    )
    conn.commit()

    return chat.id, invite.invite_link
