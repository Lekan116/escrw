import sqlite3

DB_NAME = "escrow.db"

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()


def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS escrows (
        id TEXT PRIMARY KEY,
        buyer_id INTEGER,
        seller_id INTEGER,
        group_id INTEGER,
        asset TEXT,
        status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS participants (
        escrow_id TEXT,
        user_id INTEGER,
        role TEXT,
        PRIMARY KEY (escrow_id, user_id)
    )
    """)

    conn.commit()
