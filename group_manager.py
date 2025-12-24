from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from database import cursor, conn


async def create_escrow_group(
    client: Client,
    escrow_id: str,
    creator_id: int
):
    """
    Creates a private supergroup for an escrow deal,
    assigns the bot as admin, and returns an invite link.
    """

    # ==============================
    # CREATE SUPERGROUP
    # ==============================
    chat = await client.create_supergroup(
        title=f"Escrow #{escrow_id[:8]}",
        description=(
            "🔐 Private Escrow Group\n\n"
            "Funds are held securely until both parties confirm release.\n"
            "Admin will intervene if a dispute is opened."
        )
    )

    group_id = chat.id

    # ==============================
    # PROMOTE BOT TO ADMIN
    # ==============================
    await client.promote_chat_member(
        chat_id=group_id,
        user_id=(await client.get_me()).id,
        privileges={
            "can_manage_chat": True,
            "can_delete_messages": True,
            "can_invite_users": True,
            "can_restrict_members": True,
            "can_pin_messages": True,
            "can_manage_video_chats": True
        }
    )

    # ==============================
    # CREATE INVITE LINK (LIMITED)
    # ==============================
    invite = await client.create_chat_invite_link(
        chat_id=group_id,
        member_limit=2
    )

    # ==============================
    # SAVE GROUP TO ESCROW
    # ==============================
    cursor.execute(
        "UPDATE escrows SET group_id = ? WHERE id = ?",
        (group_id, escrow_id)
    )
    conn.commit()

    return group_id, invite.invite_link
