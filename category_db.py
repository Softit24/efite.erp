import sqlite3

DB_NAME = "efite.db"


def init_categories_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                description TEXT DEFAULT ''
            )
        """)


def get_categories():
    init_categories_db()
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute(
            "SELECT id, name, description FROM categories ORDER BY name"
        ).fetchall()


def add_category(name, description=""):
    name = name.strip()
    if not name:
        return False, "Category name is required."
    init_categories_db()
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(
                "INSERT INTO categories (name, description) VALUES (?, ?)",
                (name, description.strip())
            )
        return True, "Category added successfully."
    except sqlite3.IntegrityError:
        return False, "That category already exists."


def delete_category(category_id):
    init_categories_db()
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
