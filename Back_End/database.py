import sqlite3
from contextlib import closing
from datetime import datetime

from config import DB_PATH

_db_path = DB_PATH


def use_database(path):
    """Switch to another database file (the tests use this)."""
    global _db_path
    _db_path = path


def get_connection():
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row            # rows can be read like dicts
    conn.execute("PRAGMA foreign_keys = ON")  # enforce links between tables
    return conn


def _execute(sql, params=()):
    """Run one INSERT/UPDATE/DELETE and save it."""
    with closing(get_connection()) as conn:
        with conn:                            # commits, or rolls back on error
            return conn.execute(sql, params)


def _query(sql, params=()):
    """Run a SELECT and return a list of dicts."""
    with closing(get_connection()) as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


# ---------- TABLES ----------

def create_tables():
    with closing(get_connection()) as conn:
        with conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS menu_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    price REAL NOT NULL CHECK (price > 0),
                    stock INTEGER NOT NULL CHECK (stock >= 0),
                    is_available INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_no INTEGER NOT NULL UNIQUE,
                    table_no TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    priority INTEGER NOT NULL DEFAULT 0,
                    total REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    customer_email TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL REFERENCES orders(id),
                    menu_item_id INTEGER NOT NULL REFERENCES menu_items(id),
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    price REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL
                );
            """)
            _add_missing_columns(conn)


def _add_missing_columns(conn):
    """Upgrade a database made by an older version of the app."""
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(orders)")]
    if "customer_email" not in columns:
        conn.execute("ALTER TABLE orders ADD COLUMN customer_email TEXT NOT NULL DEFAULT ''")


def seed_sample_data():
    """Add starter menu items, only if the menu is empty."""
    if load_menu_items():
        return
    sample = [
        ("Chicken Adobo", "Meals", 60, 10),
        ("Pancit Canton", "Meals", 35, 5),
        ("Iced Tea", "Drinks", 20, 0),
        ("Fried Banana", "Snacks", 15, 20),
    ]
    for name, category, price, stock in sample:
        add_menu_item(name, category, price, stock)


# ---------- MENU ITEMS ----------

def load_menu_items():
    return _query(
        "SELECT id, name, category, price, stock, is_available FROM menu_items"
    )


def add_menu_item(name, category, price, stock):
    cur = _execute(
        "INSERT INTO menu_items (name, category, price, stock) VALUES (?, ?, ?, ?)",
        (name, category, price, stock),
    )
    return cur.lastrowid                      # the new item's id


def update_menu_item(item_id, name, category, price, stock, is_available=1):
    cur = _execute(
        "UPDATE menu_items SET name=?, category=?, price=?, stock=?, is_available=? "
        "WHERE id=?",
        (name, category, price, stock, is_available, item_id),
    )
    if cur.rowcount == 0:
        raise KeyError(item_id)


def update_stock(item_id, stock):
    cur = _execute("UPDATE menu_items SET stock=? WHERE id=?", (stock, item_id))
    if cur.rowcount == 0:
        raise KeyError(item_id)


def delete_menu_item(item_id):
    cur = _execute("DELETE FROM menu_items WHERE id=?", (item_id,))
    if cur.rowcount == 0:
        raise KeyError(item_id)


# ---------- ORDERS ----------

def get_max_order_no():
    rows = _query("SELECT COALESCE(MAX(order_no), 0) AS max_no FROM orders")
    return rows[0]["max_no"]


def save_order(order_no, table_no, status, priority, total, items, customer_email=""):
    """items = list of {"menu_item_id", "quantity", "price"}. Returns created_at."""
    created_at = datetime.now().isoformat(timespec="seconds")
    with closing(get_connection()) as conn:
        with conn:                            # both inserts succeed or neither does
            cur = conn.execute(
                "INSERT INTO orders (order_no, table_no, status, priority, total, created_at, "
                "customer_email) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (order_no, str(table_no), status, priority, total, created_at, customer_email),
            )
            order_id = cur.lastrowid
            for item in items:
                conn.execute(
                    "INSERT INTO order_items (order_id, menu_item_id, quantity, price) "
                    "VALUES (?, ?, ?, ?)",
                    (order_id, item["menu_item_id"], item["quantity"], item["price"]),
                )
    return created_at


def update_order_status(order_no, status):
    cur = _execute("UPDATE orders SET status=? WHERE order_no=?", (status, order_no))
    if cur.rowcount == 0:
        raise KeyError(order_no)


def load_orders():
    """Every order, each with its 'items' list. Used once at startup."""
    orders = _query(
        "SELECT id, order_no, table_no, status, priority, total, created_at, customer_email "
        "FROM orders"
    )
    for order in orders:
        order["items"] = _query(
            "SELECT menu_item_id, quantity, price FROM order_items WHERE order_id=?",
            (order["id"],),
        )
    return orders


# ---------- ADMINS ----------

def add_admin(username, password_hash):
    _execute(
        "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
        (username, password_hash),
    )


def get_admin(username):
    rows = _query(
        "SELECT id, username, password_hash FROM admins WHERE username=?", (username,)
    )
    return rows[0] if rows else None
