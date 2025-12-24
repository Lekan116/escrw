from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# =====================
# START / MENU
# =====================
def start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Create Escrow", callback_data="create_escrow")],
        [InlineKeyboardButton("📊 My Escrows", callback_data="my_escrows")],
        [
            InlineKeyboardButton("📜 Terms", callback_data="terms"),
            InlineKeyboardButton("❓ Help", callback_data="help")
        ]
    ])

# =====================
# ESCROW ACTIONS (GROUP)
# =====================
def escrow_keyboard(is_buyer=False, is_seller=False, funded=False):
    buttons = []

    if is_buyer:
        buttons.append(InlineKeyboardButton("👛 Set Buyer Wallet", callback_data="set_buyer_wallet"))

    if is_seller:
        buttons.append(InlineKeyboardButton("👛 Set Seller Wallet", callback_data="set_seller_wallet"))

    if is_buyer:
        buttons.append(InlineKeyboardButton("💰 Select Asset", callback_data="select_asset"))

    if funded:
        buttons.append(InlineKeyboardButton("✅ Confirm Release", callback_data="confirm_release"))

    buttons.append(InlineKeyboardButton("📊 Status", callback_data="status"))
    buttons.append(InlineKeyboardButton("❌ Cancel Escrow", callback_data="cancel_escrow"))

    return InlineKeyboardMarkup([buttons])

# =====================
# ASSET SELECTION
# =====================
def asset_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("BTC", callback_data="asset_BTC"),
            InlineKeyboardButton("LTC", callback_data="asset_LTC")
        ],
        [
            InlineKeyboardButton("ETH", callback_data="asset_ETH"),
            InlineKeyboardButton("USDT", callback_data="asset_USDT")
        ]
    ])
