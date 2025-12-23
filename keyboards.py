from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Create Escrow", callback_data="create_escrow"),
            InlineKeyboardButton("My Escrows", callback_data="my_escrows")
        ],
        [
            InlineKeyboardButton("Help", callback_data="help"),
            InlineKeyboardButton("Terms", callback_data="terms")
        ]
    ])


def escrow_actions(is_buyer=False, is_seller=False, funded=False):
    buttons = []

    if is_buyer and not funded:
        buttons.append(
            InlineKeyboardButton("Check Deposit", callback_data="check_deposit")
        )

    if funded and (is_buyer or is_seller):
        buttons.append(
            InlineKeyboardButton("Confirm Release", callback_data="confirm_release")
        )

    buttons.append(
        InlineKeyboardButton("Open Dispute", callback_data="open_dispute")
    )

    return InlineKeyboardMarkup([buttons])
