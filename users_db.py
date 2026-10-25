import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = Path(__file__).resolve().parent / "efite.db"


def get_connection():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_users_table():
    with get_connection() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'Employee'
                    CHECK(role IN ('Admin', 'Employee', 'Customer')),
                status TEXT NOT NULL DEFAULT 'Active'
                    CHECK(status IN ('Active', 'Inactive')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def list_users():
    with get_connection() as con:
        return con.execute("""
            SELECT id, full_name, username, role, status, created_at
            FROM users
            ORDER BY id DESC
        """).fetchall()


def add_user(full_name, username, password, role, status):
    full_name = full_name.strip()
    username = username.strip()

    if not full_name or not username or not password:
        raise ValueError("Name, username and password are required.")

    if role not in ("Admin", "Employee", "Customer"):
        raise ValueError("Invalid role.")

    if status not in ("Active", "Inactive"):
        raise ValueError("Invalid account status.")

    password_hash = generate_password_hash(password)

    try:
        with get_connection() as con:
            con.execute("""
                INSERT INTO users
                    (full_name, username, password_hash, role, status)
                VALUES (?, ?, ?, ?, ?)
            """, (full_name, username, password_hash, role, status))
    except sqlite3.IntegrityError as exc:
        raise ValueError("That username already exists.") from exc


def verify_user(username, password):
    with get_connection() as con:
        user = con.execute("""
            SELECT id, full_name, username, password_hash, role, status
            FROM users
            WHERE username = ? COLLATE NOCASE
        """, (username.strip(),)).fetchone()

    if (
        user
        and user["status"] == "Active"
        and check_password_hash(user["password_hash"], password)
    ):
        return {
            "id": user["id"],
            "full_name": user["full_name"],
            "username": user["username"],
            "role": user["role"],
        }

    return None


def delete_user(user_id):
    with get_connection() as con:
        con.execute("DELETE FROM users WHERE id = ?", (user_id,))
