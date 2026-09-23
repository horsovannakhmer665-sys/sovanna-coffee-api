from flask import Flask, jsonify, request
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

            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    address TEXT NOT NULL,
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'ថ្មី'
                )
            """)

        conn.commit()

init_database()


# GET - បង្ហាញទំនិញទាំងអស់
@app.route("/api/products", methods=["GET"])
def products():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, category, sell_price, stock, image
                FROM products
                ORDER BY id DESC
            """)

            rows = cur.fetchall()

    result = []

    for row in rows:
        result.append({
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "sell_price": row[3],
            "stock": row[4],
            "image": row[5]
        })

    return jsonify(result)


# POST - បញ្ចូលទំនិញថ្មី
@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.get_json()

    name = data.get("name")
    category = data.get("category")
    buy_price = data.get("buy_price", 0)
    sell_price = data.get("sell_price", 0)
    stock = data.get("stock", 0)
    image = data.get("image")

    if not name:
        return jsonify({
            "error": "ត្រូវបញ្ចូលឈ្មោះទំនិញ"
        }), 400

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO products
                (name, category, buy_price, sell_price, stock, image)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                name,
                category,
                buy_price,
                sell_price,
                stock,
                image
            ))

            product_id = cur.fetchone()[0]

        conn.commit()

    return jsonify({
        "message": "បានបញ្ចូលទំនិញ",
        "id": product_id
    }), 201
@app.route("/api/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json()

    name = data.get("name")
    category = data.get("category")
    buy_price = data.get("buy_price", 0)
    sell_price = data.get("sell_price", 0)
    stock = data.get("stock", 0)
    image = data.get("image")

    if not name:
        return jsonify({
            "error": "ត្រូវបញ្ចូលឈ្មោះទំនិញ"
        }), 400

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            cur.execute("""
                UPDATE products
                SET
                    name = %s,
                    category = %s,
                    buy_price = %s,
                    sell_price = %s,
                    stock = %s,
                    image = %s
                WHERE id = %s
            """, (
                name,
                category,
                buy_price,
                sell_price,
                stock,
                image,
                product_id
            ))

            if cur.rowcount == 0:
                return jsonify({
                    "error": "រកមិនឃើញទំនិញ"
                }), 404

        conn.commit()

    return jsonify({
        "message": "បានកែទំនិញ",
        "id": product_id
    })


@app.route("/")
def home():
    return "Sovanna Coffee API is running"


if __name__ == "__main__":
    app.run(debug=True)