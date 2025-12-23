import os
from database import cursor

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def get_role(escrow_id: str, user_id: int):
    cursor.execute(
        "SELECT role FROM escrow_participants WHERE escrow_id = ? AND user_id = ?",
        (escrow_id, user_id)
    )
    row = cursor.fetchone()
    return row[0] if row else None


def require_role(escrow_id: str, user_id: int, allowed: list):
    role = get_role(escrow_id, user_id)
    return role in allowed
