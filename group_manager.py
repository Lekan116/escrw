from pyrogram import Client
from pyrogram.enums import ChatType
from database import cursor, conn

async def create_escrow_group(app: Client, escrow_id: str, buyer_id: int):
    """
    Creates a private supergroup for the escrow
    """

    chat = await app.create_supergroup(
        title=f"Escrow Deal #{escrow_id[:8]}",
        description="Private escrow group. Funds are held until release."
    )

    # Generate invite link
    invite = await app.create_chat_invite_link(
        chat.id,
        member_limit=2
    )

    # Bind group to escrow
    cursor.execute(
        "UPDATE escrows SET group_id = ? WHERE id = ?",
        (chat.id, escrow_id)
    )
    conn.commit()

    return chat.id, invite.invite_link
