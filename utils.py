import os

ASSET_WALLETS = {
    "BTC": os.getenv("BTC_WALLET"),
    "ETH": os.getenv("ETH_WALLET"),
    "USDT": os.getenv("USDT_WALLET"),
    "LTC": os.getenv("LTC_WALLET"),
}


def escrow_terms():
    return (
        "📜 *P2P ESCROW TERMS*\n\n"
        "1️⃣ Buyer must fund escrow wallet\n"
        "2️⃣ Seller delivers only after funding\n"
        "3️⃣ Funds released when both agree\n"
        "4️⃣ Admin may intervene in disputes\n"
        "5️⃣ Bot never holds private keys\n\n"
        "⚠️ Always double-check wallet address.\n"
        "⚠️ Sending to wrong address is irreversible."
    )


def help_text():
    return (
        "❓ *HOW P2P ESCROWBOT WORKS*\n\n"
        "• Buyer creates escrow\n"
        "• Bot opens private group\n"
        "• Seller joins via invite link\n"
        "• Buyer selects asset\n"
        "• Buyer sends funds\n"
        "• Seller delivers\n"
        "• Escrow completes safely\n\n"
        "🔒 Trustless • Transparent • Secure"
    )
