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

            # Products
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

            # Orders
            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    address TEXT NOT NULL,
                    total DOUBLE PRECISION DEFAULT 0,
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'ថ្មី'
                )
            """)

            # Add total to old database if it does not exist
            cur.execute("""
                ALTER TABLE orders
                ADD COLUMN IF NOT EXISTS total DOUBLE PRECISION DEFAULT 0
            """)
            # Order items
            cur.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    sell_price DOUBLE PRECISION DEFAULT 0,
                    quantity INTEGER DEFAULT 1
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
@app.route("/api/orders", methods=["POST"])
def create_order():

    data = request.get_json() or {}

    customer_name = data.get("customer_name")
    phone = data.get("phone")
    address = data.get("address")

    items = data.get("items", [])

    if not customer_name or not phone or not address:
        return jsonify({
            "error": "សូមបំពេញឈ្មោះ ទូរស័ព្ទ និងអាសយដ្ឋាន"
        }), 400

    total = 0

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            # ពិនិត្យទំនិញ និងយកតម្លៃពិតពី Database
            checked_items = []

            for item in items:

                product_id = int(item.get("id", 0))
                quantity = int(item.get("quantity", 0))

                if product_id <= 0 or quantity <= 0:
                    return jsonify({
                        "error": "ទិន្នន័យទំនិញមិនត្រឹមត្រូវ"
                    }), 400

                cur.execute("""
                    SELECT name, sell_price, stock
                    FROM products
                    WHERE id = %s
                """, (product_id,))

                product = cur.fetchone()

                if not product:
                    return jsonify({
                        "error": f"រកមិនឃើញទំនិញ ID {product_id}"
                    }), 404

                product_name = product[0]
                price = float(product[1])
                stock = int(product[2])

                if quantity > stock:
                    return jsonify({
                        "error": f"{product_name} ស្តុកមិនគ្រប់"
                    }), 400

                total += quantity * price

                checked_items.append({
                    "name": product_name,
                    "price": price,
                    "quantity": quantity
                })

            # បង្កើត Order
            cur.execute("""
                INSERT INTO orders
                (customer_name, phone, address, total)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
                customer_name,
                phone,
                address,
                total
            ))

            order_id = cur.fetchone()[0]

            # រក្សាទុកទំនិញក្នុង Order
            for item in checked_items:

                cur.execute("""
                    INSERT INTO order_items
                    (order_id, product_name, sell_price, quantity)
                    VALUES (%s, %s, %s, %s)
                """, (
                    order_id,
                    item["name"],
                    item["price"],
                    item["quantity"]
                ))

        conn.commit()

    return jsonify({
        "message": "បានទទួលកម្ម៉ង់",
        "order_id": order_id,
        "total": total
    }), 201

# PUT - កែទំនិញ
@app.route("/api/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):

    data = request.get_json() or {}

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

# GET - មើលកម្ម៉ង់ Online
@app.route("/api/orders", methods=["GET"])
def get_orders():

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    customer_name,
                    phone,
                    address,
                    total,
                    order_date,
                    status
                FROM orders
                ORDER BY id DESC
            """)

            rows = cur.fetchall()

            result = []

            for row in rows:

                order_id = row[0]

                # ទាញទំនិញក្នុង Order
                cur.execute("""
                    SELECT
                        product_name,
                        sell_price,
                        quantity
                    FROM order_items
                    WHERE order_id = %s
                    ORDER BY id
                """, (order_id,))

                item_rows = cur.fetchall()

                items = []

                for item in item_rows:
                    items.append({
                        "name": item[0],
                        "sell_price": item[1],
                        "quantity": item[2]
                    })

                result.append({
                    "id": row[0],
                    "customer_name": row[1],
                    "phone": row[2],
                    "address": row[3],
                    "total": row[4],
                    "order_date": str(row[5]),
                    "status": row[6],
                    "items": items
                })

    return jsonify(result)

# Home
@app.route("/")
def home():
    return "Sovanna Coffee API is running"


if __name__ == "__main__":
    app.run(debug=True)