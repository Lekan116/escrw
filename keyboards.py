from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ===== MAIN MENU =====
def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🆕 Create Escrow", callback_data="create_escrow"),
            InlineKeyboardButton("📂 My Escrows", callback_data="my_escrows")
        ],
        [
            InlineKeyboardButton("📖 Help", callback_data="help"),
            InlineKeyboardButton("📜 Terms", callback_data="terms")
        ]
    ])


# ===== ESCROW SETUP =====
def escrow_setup_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👤 Join as Buyer", callback_data="join_buyer"),
            InlineKeyboardButton("🧍 Join as Seller", callback_data="join_seller")
        ],
        [
            InlineKeyboardButton("💰 Select Asset", callback_data="select_asset"),
        ],
        [
            InlineKeyboardButton("❌ Cancel Escrow", callback_data="cancel_escrow")
        ]
    ])


# ===== ASSET SELECTION =====
def asset_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("₿ BTC", callback_data="asset_BTC"),
            InlineKeyboardButton("Ξ ETH", callback_data="asset_ETH")
        ],
        [
            InlineKeyboardButton("💲 USDT", callback_data="asset_USDT"),
            InlineKeyboardButton("Ł LTC", callback_data="asset_LTC")
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="back_to_escrow")
        ]
    ])


# ===== FUNDED / ACTIVE ESCROW =====
def escrow_actions(is_buyer=False, is_seller=False, funded=False):
    buttons = []

    if is_buyer and not funded:
        buttons.append(
            InlineKeyboardButton("🔍 Check Deposit", callback_data="check_deposit")
        )

    if funded and (is_buyer or is_seller):
        buttons.append(
            InlineKeyboardButton("✅ Confirm Release", callback_data="confirm_release")
        )

    buttons.append(
        InlineKeyboardButton("⚠️ Open Dispute", callback_data="open_dispute")
    )

    return InlineKeyboardMarkup([buttons])


# ===== CONFIRM RELEASE =====
def confirm_release_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, Release", callback_data="release_yes"),
            InlineKeyboardButton("❌ No", callback_data="release_no")
        ]
    ])


# ===== ADMIN =====
def admin_panel():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚖️ Force Release", callback_data="admin_release"),
            InlineKeyboardButton("🛑 Cancel Escrow", callback_data="admin_cancel")
        ]
    ])
