from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ==============================
# START / HOME
# ==============================
def start_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🆕 Create Escrow", callback_data="escrow:create"),
                InlineKeyboardButton("📂 My Escrows", callback_data="escrow:list")
            ],
            [
                InlineKeyboardButton("📜 Terms", callback_data="info:terms"),
                InlineKeyboardButton("❓ Help", callback_data="info:help")
            ]
        ]
    )


# ==============================
# ESCROW SETUP
# ==============================
def escrow_setup_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("👤 Set Buyer", callback_data="escrow:set_buyer"),
                InlineKeyboardButton("🧍 Set Seller", callback_data="escrow:set_seller")
            ],
            [
                InlineKeyboardButton("💰 Select Asset", callback_data="escrow:set_asset"),
            ],
            [
                InlineKeyboardButton("❌ Cancel Escrow", callback_data="escrow:cancel")
            ]
        ]
    )


# ==============================
# ASSET SELECTION
# ==============================
def asset_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("₿ BTC", callback_data="asset:BTC"),
                InlineKeyboardButton("Ł LTC", callback_data="asset:LTC")
            ],
            [
                InlineKeyboardButton("Ξ ETH", callback_data="asset:ETH"),
                InlineKeyboardButton("💵 USDT", callback_data="asset:USDT")
            ]
        ]
    )


# ==============================
# ACTIVE ESCROW CONTROLS
# ==============================
def escrow_action_keyboard(
    is_buyer=False,
    is_seller=False,
    funded=False,
    is_admin=False
):
    buttons = []

    # Buyer actions
    if is_buyer and not funded:
        buttons.append(
            InlineKeyboardButton("🔍 Check Deposit", callback_data="escrow:check_deposit")
        )

    # Release confirmation
    if funded and (is_buyer or is_seller):
        buttons.append(
            InlineKeyboardButton("✅ Confirm Release", callback_data="escrow:confirm_release")
        )

    # Dispute
    buttons.append(
        InlineKeyboardButton("⚠️ Open Dispute", callback_data="escrow:dispute")
    )

    # Admin override
    if is_admin:
        buttons.append(
            InlineKeyboardButton("🛑 Admin Resolve", callback_data="admin:resolve")
        )

    return InlineKeyboardMarkup([buttons])


# ==============================
# CONFIRM RELEASE
# ==============================
def confirm_release_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Yes, Release", callback_data="release:yes"),
                InlineKeyboardButton("❌ No", callback_data="release:no")
            ]
        ]
    )
