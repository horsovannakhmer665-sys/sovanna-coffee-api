from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3
import os
import database

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BASE_DIR, "shop.db")


@app.route("/api/products")
def products():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT name, category, sell_price, stock, image
        FROM products
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    result = []

    for row in rows:
        result.append({
            "name": row["name"],
            "category": row["category"],
            "sell_price": row["sell_price"],
            "stock": row["stock"],
            "image": row["image"]
        })

    return jsonify(result)


@app.route("/")
def home():
    return "Sovanna Coffee API is running"


if __name__ == "__main__":
    app.run(debug=True)