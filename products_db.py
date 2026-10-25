import sqlite3

DB_NAME = "efite.db"


def init_db():
    with sqlite3.connect(DB_NAME) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT NOT NULL UNIQUE,
                price REAL NOT NULL DEFAULT 0,
                quantity INTEGER NOT NULL DEFAULT 0,
                url TEXT NOT NULL DEFAULT '',
                installation_fees REAL NOT NULL DEFAULT 0
            )
        """)
        cols = [r[1] for r in con.execute("PRAGMA table_info(products)")]
        if "url" not in cols:
            con.execute("ALTER TABLE products ADD COLUMN url TEXT NOT NULL DEFAULT ''")
        if "installation_fees" not in cols:
            con.execute("ALTER TABLE products ADD COLUMN installation_fees REAL NOT NULL DEFAULT 0")


def get_products():
    init_db()
    with sqlite3.connect(DB_NAME) as con:
        con.row_factory = sqlite3.Row
        return con.execute("SELECT * FROM products ORDER BY id DESC").fetchall()


def add_product(
    name, sku, price=0, quantity=0, url="",
    installation_fees=0, monthly_service_fees=0
):
    init_db()
    name, sku, url = name.strip(), sku.strip().upper(), url.strip()

    if not name or not sku:
        return False, "Product name and SKU are required."

    try:
        price = float(price)
        quantity = int(quantity)
        installation_fees = float(installation_fees)
        monthly_service_fees = float(monthly_service_fees)

        if (price < 0 or quantity < 0 or
                installation_fees < 0 or monthly_service_fees < 0):
            return False, "Values cannot be negative."

        with sqlite3.connect(DB_NAME) as con:
            con.execute(
                """INSERT INTO products
                (name, sku, price, quantity, url,
                 installation_fees, monthly_service_fees)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (name, sku, price, quantity, url,
                 installation_fees, monthly_service_fees)
            )

        return True, "Product added successfully."

    except sqlite3.IntegrityError:
        return False, f"SKU '{sku}' already exists."
    except (ValueError, TypeError):
        return False, "Enter valid numeric values for prices and fees."


def update_product(
    product_id, name, sku, price, quantity, url,
    installation_fees, monthly_service_fees=0
):
    init_db()
    name, sku, url = name.strip(), sku.strip().upper(), url.strip()

    try:
        price = float(price)
        quantity = int(quantity)
        installation_fees = float(installation_fees)
        monthly_service_fees = float(monthly_service_fees)

        if (not name or not sku or price < 0 or quantity < 0 or
                installation_fees < 0 or monthly_service_fees < 0):
            return False, "Check product details and numeric values."

        with sqlite3.connect(DB_NAME) as con:
            con.execute(
                """UPDATE products
                SET name=?, sku=?, price=?, quantity=?, url=?,
                    installation_fees=?, monthly_service_fees=?
                WHERE id=?""",
                (name, sku, price, quantity, url,
                 installation_fees, monthly_service_fees, product_id)
            )

        return True, "Product updated successfully."

    except sqlite3.IntegrityError:
        return False, f"SKU '{sku}' already exists."
    except (ValueError, TypeError):
        return False, "Enter valid numeric values for prices and fees."


def delete_product(product_id):
    init_db()
    with sqlite3.connect(DB_NAME) as con:
        con.execute("DELETE FROM products WHERE id=?", (product_id,))
