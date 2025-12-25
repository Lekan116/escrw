from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🆕 Create Escrow", callback_data="escrow:create")],
        [
            InlineKeyboardButton("📜 Terms", callback_data="info:terms"),
            InlineKeyboardButton("❓ Help", callback_data="info:help")
        ]
    ])


def escrow_group_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Select Asset", callback_data="escrow:asset")],
        [InlineKeyboardButton("📊 Status", callback_data="escrow:status")],
        [InlineKeyboardButton("⚖️ Cancel Escrow", callback_data="escrow:cancel")]
    ])


def asset_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("BTC", callback_data="asset:BTC"),
            InlineKeyboardButton("ETH", callback_data="asset:ETH")
        ],
        [
            InlineKeyboardButton("USDT", callback_data="asset:USDT"),
            InlineKeyboardButton("LTC", callback_data="asset:LTC")
        ]
    ])
