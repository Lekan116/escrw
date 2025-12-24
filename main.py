import os
import asyncio
from dotenv import load_dotenv

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from keep_alive import keep_alive
from callbacks import (
    start_callback,
    create_escrow,
    select_asset,
    set_asset,
    check_deposit,
    confirm_release,
    release_yes,
    release_no,
)
from database import init_db


# =========================
# LOAD ENV
# =========================
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")


# =========================
# INIT BOT
# =========================
app = Client(
    "escrow_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# =========================
# STARTUP
# =========================
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    await message.reply(
        "👋 Welcome to Escrow Bot\n\n"
        "Use the buttons below to create a secure escrow.",
        reply_markup=None
    )


# =========================
# CALLBACK ROUTER
# =========================
@app.on_callback_query()
async def callback_router(client, cq: CallbackQuery):
    data = cq.data

    # HOME
    if data == "home:start":
        await start_callback(client, cq)

    # ESCROW
    elif data == "escrow:create":
        await create_escrow(client, cq)

    elif data == "escrow:set_asset":
        await select_asset(client, cq)

    elif data.startswith("asset:"):
        await set_asset(client, cq)

    elif data == "escrow:check_deposit":
        await check_deposit(client, cq)

    elif data == "escrow:confirm_release":
        await confirm_release(client, cq)

    # RELEASE
    elif data == "release:yes":
        await release_yes(client, cq)

    elif data == "release:no":
        await release_no(client, cq)

    else:
        await cq.answer("Unknown action", show_alert=True)


# =========================
# MAIN ENTRY
# =========================
async def main():
    init_db()
    keep_alive()
    await app.start()
    print("🚀 Escrow Bot is LIVE")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
