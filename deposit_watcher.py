import asyncio
from database import cursor, conn
from utils import confirm_deposit
from pyrogram import Client

CHECK_INTERVAL = 60  # seconds (safe for APIs)

async def deposit_watcher(app: Client):
    await app.wait_until_ready()

    while True:
        try:
            cursor.execute(
                """
                SELECT 
                    e.id,
                    e.group_id,
                    e.asset,
                    w.address
                FROM escrows e
                JOIN wallets w
                    ON e.buyer_id = w.user_id
                    AND e.asset = w.asset
                WHERE e.status = 'awaiting_deposit'
                """
            )

            escrows = cursor.fetchall()

            for escrow_id, group_id, asset, address in escrows:
                confirmed = confirm_deposit(escrow_id, address)

                if confirmed:
                    await app.send_message(
                        group_id,
                        "Deposit confirmed.\n\n"
                        "The seller may proceed with delivery.\n"
                        "Once complete, both parties must confirm release."
                    )

            await asyncio.sleep(CHECK_INTERVAL)

        except Exception as e:
            print(f"[DEPOSIT WATCHER ERROR] {e}")
            await asyncio.sleep(CHECK_INTERVAL)
