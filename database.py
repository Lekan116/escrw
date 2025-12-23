import sqlite3

DB_NAME = "escrow.db"

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

# =========================================================
# ESCROWS (CORE)
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS escrows (
    id TEXT PRIMARY KEY,

    buyer_id INTEGER NOT NULL,
    seller_id INTEGER,
    group_id INTEGER,

    asset TEXT,
    amount REAL,
    fee REAL,
    net_amount REAL,

    status TEXT NOT NULL,
    funded INTEGER DEFAULT 0,

    buyer_confirmed INTEGER DEFAULT 0,
    seller_confirmed INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
)
""")

# =========================================================
# ESCROW PARTICIPANTS (ROLES)
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS escrow_participants (
    escrow_id TEXT,
    user_id INTEGER,
    role TEXT,

    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (escrow_id, user_id)
)
""")

# =========================================================
# WALLETS
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS wallets (
    user_id INTEGER,
    asset TEXT,
    address TEXT,

    verified INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, asset)
)
""")

# =========================================================
# TRANSACTIONS (ON-CHAIN)
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    escrow_id TEXT,
    asset TEXT,
    address TEXT,

    tx_hash TEXT UNIQUE,
    amount REAL,

    confirmations INTEGER DEFAULT 0,
    confirmed INTEGER DEFAULT 0,

    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# =========================================================
# DISPUTES
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS disputes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    escrow_id TEXT,
    opened_by INTEGER,
    reason TEXT,

    status TEXT DEFAULT 'open',
    resolved_by INTEGER,
    resolution TEXT,

    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
)
""")

# =========================================================
# AUDIT LOGS (IMMUTABLE)
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    escrow_id TEXT,
    action TEXT,
    performed_by INTEGER,

    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# =========================================================
# SETTINGS (GLOBAL CONFIG)
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

# Defaults (safe to re-run)
cursor.execute("INSERT OR IGNORE INTO settings VALUES ('fee_percent', '5')")
cursor.execute("INSERT OR IGNORE INTO settings VALUES ('min_fee', '5')")
cursor.execute("INSERT OR IGNORE INTO settings VALUES ('required_confirmations', '2')")

# =========================================================
# SESSIONS (SMART UI FLOW)
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS sessions (
    user_id INTEGER PRIMARY KEY,

    escrow_id TEXT,
    state TEXT,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# =========================================================
# FINALIZE
# =========================================================

conn.commit()
