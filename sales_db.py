import sqlite3
from products_db import init_db

DB_NAME = "efite.db"

def init_sales_db():
    init_db()
    with sqlite3.connect(DB_NAME) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total REAL NOT NULL,
                sale_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        con.commit()

def get_sales():
    init_sales_db()
    with sqlite3.connect(DB_NAME) as con:
        con.row_factory = sqlite3.Row
        return [dict(row) for row in con.execute(
            "SELECT * FROM sales ORDER BY id DESC"
        ).fetchall()]

def record_sale(product_id, quantity):
    init_sales_db()
    if quantity < 1:
        return False, "Quantity must be at least 1."

    with sqlite3.connect(DB_NAME) as con:
        con.row_factory = sqlite3.Row
        con.execute("BEGIN IMMEDIATE")
        product = con.execute(
            "SELECT id, name, price, quantity FROM products WHERE id=?",
            (product_id,)
        ).fetchone()

        if product is None:
            return False, "Product not found."

        if quantity > int(product["quantity"]):
            return False, "Not enough stock available."

        price = float(product["price"])
        total = round(price * quantity, 2)

        con.execute(
            "UPDATE products SET quantity=quantity-? WHERE id=?",
            (quantity, product_id)
        )
        con.execute("""
            INSERT INTO sales
            (product_id, product_name, quantity, unit_price, total)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, product["name"], quantity, price, total))
        con.commit()

    return True, "Sale recorded successfully."
