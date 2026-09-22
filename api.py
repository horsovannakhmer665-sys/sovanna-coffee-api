from flask import Flask, jsonify
from flask_cors import CORS
import os
import psycopg

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get("DATABASE_URL")


def init_database():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT,
                    buy_price DOUBLE PRECISION DEFAULT 0,
                    sell_price DOUBLE PRECISION DEFAULT 0,
                    stock INTEGER DEFAULT 0,
                    image TEXT
                )
            """)
        conn.commit()


init_database()


@app.route("/api/products")
def products():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT name, category, sell_price, stock, image
                FROM products
                ORDER BY id DESC
            """)

            rows = cur.fetchall()

    result = []

    for row in rows:
        result.append({
            "name": row[0],
            "category": row[1],
            "sell_price": row[2],
            "stock": row[3],
            "image": row[4]
        })

    return jsonify(result)


@app.route("/")
def home():
    return "Sovanna Coffee API is running"


if __name__ == "__main__":
    app.run(debug=True)