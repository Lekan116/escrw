import os
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters

from database import init_db
from keep_alive import keep_alive
from callbacks import (
    start_callback,
    create_escrow,
    select_asset,
    set_asset,
    show_terms,
    show_help
)

load_dotenv()

app = Client(
    "p2p_escrowbot",
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN")
)


@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await start_callback(client, message)


@app.on_callback_query()
async def router(client, cq):
    data = cq.data

    if data == "escrow:create":
        await create_escrow(client, cq)

    elif data == "escrow:asset":
        await select_asset(client, cq)

    elif data.startswith("asset:"):
        await set_asset(client, cq)

    elif data == "info:terms":
        await show_terms(client, cq)

    elif data == "info:help":
        await show_help(client, cq)

    await cq.answer()


async def main():
    init_db()
    keep_alive()
    await app.start()
    print("🚀 P2P EscrowBot is LIVE")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
