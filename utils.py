import os
import re
import requests
from decimal import Decimal
from database import cursor, conn

# =========================================================
# CONFIG
# =========================================================

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")

SOCHAIN_BASE = "https://sochain.com/api/v2"
ETHERSCAN_BASE = "https://api.etherscan.io/api"

USDT_CONTRACT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"

DEFAULT_CONFIRMATIONS = {
    "BTC": 2,
    "LTC": 2,
    "ETH": 12,
    "USDT": 12
}

# =========================================================
# SETTINGS / FEES
# =========================================================

def get_setting(key: str, default=None):
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row[0] if row else default


def calculate_fee(amount: float):
    """
    Fee logic (configurable via DB):
    - Percent fee (default 5%)
    - Minimum fee (default $5)
    """
    percent = Decimal(get_setting("fee_percent", "5")) / 100
    min_fee = Decimal(get_setting("min_fee", "5"))

    amount = Decimal(str(amount))
    fee = max(amount * percent, min_fee)
    net = amount - fee

    return float(round(fee, 8)), float(round(net, 8))

# =========================================================
# ADDRESS VALIDATION
# =========================================================

def validate_address(asset: str, address: str) -> bool:
    patterns = {
        "BTC": r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}$",
        "LTC": r"^(ltc1|[LM3])[a-zA-HJ-NP-Z0-9]{26,39}$",
        "ETH": r"^0x[a-fA-F0-9]{40}$",
        "USDT": r"^0x[a-fA-F0-9]{40}$"
    }
    return bool(re.match(patterns.get(asset, ""), address))

# =========================================================
# WALLET HELPERS
# =========================================================

def get_user_wallet(user_id: int, asset: str):
    cursor.execute(
        "SELECT address FROM wallets WHERE user_id = ? AND asset = ?",
        (user_id, asset)
    )
    row = cursor.fetchone()
    return row[0] if row else None


def set_user_wallet(user_id: int, asset: str, address: str):
    cursor.execute(
        """
        INSERT OR REPLACE INTO wallets (user_id, asset, address, verified)
        VALUES (?, ?, ?, 1)
        """,
        (user_id, asset, address)
    )
    conn.commit()

# =========================================================
# BALANCE FETCHING
# =========================================================

def get_balance(asset: str, address: str):
    try:
        if asset in ("BTC", "LTC"):
            url = f"{SOCHAIN_BASE}/get_address_balance/{asset}/{address}"
            r = requests.get(url, timeout=10)
            data = r.json()
            return float(data["data"]["confirmed_balance"])

        if asset == "ETH":
            r = requests.get(
                ETHERSCAN_BASE,
                params={
                    "module": "account",
                    "action": "balance",
                    "address": address,
                    "tag": "latest",
                    "apikey": ETHERSCAN_API_KEY
                },
                timeout=10
            )
            return int(r.json()["result"]) / 1e18

        if asset == "USDT":
            r = requests.get(
                ETHERSCAN_BASE,
                params={
                    "module": "account",
                    "action": "tokenbalance",
                    "contractaddress": USDT_CONTRACT,
                    "address": address,
                    "tag": "latest",
                    "apikey": ETHERSCAN_API_KEY
                },
                timeout=10
            )
            return int(r.json()["result"]) / 1e6

    except Exception as e:
        print(f"[BALANCE ERROR] {asset}: {e}")

    return None

# =========================================================
# TRANSACTION DETECTION
# =========================================================

def detect_transactions(asset: str, address: str):
    """
    Returns:
    [
        {
            tx_hash,
            amount,
            confirmations
        }
    ]
    """
    txs = []

    try:
        if asset in ("BTC", "LTC"):
            url = f"{SOCHAIN_BASE}/get_tx_received/{asset}/{address}"
            r = requests.get(url, timeout=10)
            for tx in r.json()["data"]["txs"]:
                txs.append({
                    "tx_hash": tx["txid"],
                    "amount": float(tx["value"]),
                    "confirmations": int(tx["confirmations"])
                })

        elif asset == "ETH":
            r = requests.get(
                ETHERSCAN_BASE,
                params={
                    "module": "account",
                    "action": "txlist",
                    "address": address,
                    "startblock": 0,
                    "endblock": 99999999,
                    "sort": "desc",
                    "apikey": ETHERSCAN_API_KEY
                },
                timeout=10
            )
            for tx in r.json()["result"]:
                if tx["to"].lower() == address.lower():
                    txs.append({
                        "tx_hash": tx["hash"],
                        "amount": int(tx["value"]) / 1e18,
                        "confirmations": int(tx["confirmations"])
                    })

        elif asset == "USDT":
            r = requests.get(
                ETHERSCAN_BASE,
                params={
                    "module": "account",
                    "action": "tokentx",
                    "contractaddress": USDT_CONTRACT,
                    "address": address,
                    "sort": "desc",
                    "apikey": ETHERSCAN_API_KEY
                },
                timeout=10
            )
            for tx in r.json()["result"]:
                if tx["to"].lower() == address.lower():
                    txs.append({
                        "tx_hash": tx["hash"],
                        "amount": int(tx["value"]) / 1e6,
                        "confirmations": int(tx["confirmations"])
                    })

    except Exception as e:
        print(f"[TX ERROR] {asset}: {e}")

    return txs

# =========================================================
# DEPOSIT CONFIRMATION (ESCROW-LEVEL)
# =========================================================

def confirm_deposit(escrow_id: str, address: str) -> bool:
    """
    Detects and confirms deposit.
    Updates:
    - transactions table
    - escrows.funded
    - escrows.status
    """
    cursor.execute(
        "SELECT asset, amount FROM escrows WHERE id = ?",
        (escrow_id,)
    )
    row = cursor.fetchone()
    if not row:
        return False

    asset, expected_amount = row
    expected_amount = float(expected_amount)

    required_conf = int(
        get_setting(
            "required_confirmations",
            DEFAULT_CONFIRMATIONS.get(asset, 2)
        )
    )

    for tx in detect_transactions(asset, address):
        if tx["amount"] >= expected_amount and tx["confirmations"] >= required_conf:
            cursor.execute(
                """
                INSERT OR IGNORE INTO transactions
                (escrow_id, asset, address, tx_hash, amount, confirmations, confirmed)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    escrow_id,
                    asset,
                    address,
                    tx["tx_hash"],
                    tx["amount"],
                    tx["confirmations"]
                )
            )

            cursor.execute(
                """
                UPDATE escrows
                SET funded = 1, status = 'funded'
                WHERE id = ?
                """,
                (escrow_id,)
            )

            conn.commit()
            return True

    return False
