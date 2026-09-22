import sqlite3
import os

DB_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "shop.db"
)

conn = sqlite3.connect(DB_FILE)

conn.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    buy_price REAL DEFAULT 0,
    sell_price REAL DEFAULT 0,
    stock INTEGER DEFAULT 0,
    image TEXT
)
""")

conn.commit()
conn.close()