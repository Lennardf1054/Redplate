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
                CREATE TABLE IF NOT EXISTS shops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS menu_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    price REAL NOT NULL CHECK (price > 0),
                    stock INTEGER NOT NULL CHECK (stock >= 0),
                    is_available INTEGER NOT NULL DEFAULT 1,
                    shop_id INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_no INTEGER NOT NULL UNIQUE,
                    table_no TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    priority INTEGER NOT NULL DEFAULT 0,
                    total REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    customer_email TEXT NOT NULL DEFAULT '',
                    shop_id INTEGER NOT NULL DEFAULT 0
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
    wanted = {
        "orders": [("customer_email", "TEXT NOT NULL DEFAULT ''"),
                   ("shop_id", "INTEGER NOT NULL DEFAULT 0")],
        "menu_items": [("shop_id", "INTEGER NOT NULL DEFAULT 0")],
    }
    for table, columns in wanted.items():
        existing = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})")]
        for name, definition in columns:
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


# ---------- SHOPS (each shop is also a login account) ----------

def add_shop(name, password_hash):
    """Creates the shop and its login in one go. Returns the new shop id."""
    cur = _execute("INSERT INTO shops (name, password_hash) VALUES (?, ?)", (name, password_hash))
    return cur.lastrowid


def load_shops():
    return _query("SELECT id, name, password_hash FROM shops")


def update_shop_password(shop_id, password_hash):
    cur = _execute("UPDATE shops SET password_hash=? WHERE id=?", (password_hash, shop_id))
    if cur.rowcount == 0:
        raise KeyError(shop_id)

def delete_shop(shop_id):
    """Remove a shop with its menu items, its orders and their lines, all or nothing."""
    with closing(get_connection()) as conn:
        with conn:
            conn.execute("DELETE FROM order_items WHERE order_id IN "
                         "(SELECT id FROM orders WHERE shop_id=?)", (shop_id,))
            conn.execute("DELETE FROM orders WHERE shop_id=?", (shop_id,))
            conn.execute("DELETE FROM menu_items WHERE shop_id=?", (shop_id,))
            cur = conn.execute("DELETE FROM shops WHERE id=?", (shop_id,))
            if cur.rowcount == 0:
                raise KeyError(shop_id)           # undoes the deletes above

def rename_shop(shop_id, name):
    cur = _execute("UPDATE shops SET name=? WHERE id=?", (name, shop_id))
    if cur.rowcount == 0:
        raise KeyError(shop_id)

def has_unassigned_rows():
    """True if there are menu items or orders from the old one-shop version."""
    rows = _query(
        "SELECT (SELECT COUNT(*) FROM menu_items WHERE shop_id=0) + "
        "(SELECT COUNT(*) FROM orders WHERE shop_id=0) AS n"
    )
    return rows[0]["n"] > 0


def assign_unassigned_rows(shop_id):
    with closing(get_connection()) as conn:
        with conn:
            conn.execute("UPDATE menu_items SET shop_id=? WHERE shop_id=0", (shop_id,))
            conn.execute("UPDATE orders SET shop_id=? WHERE shop_id=0", (shop_id,))


# ---------- MENU ITEMS ----------

def load_menu_items():
    return _query(
        "SELECT id, shop_id, name, category, price, stock, is_available FROM menu_items"
    )


def add_menu_item(shop_id, name, category, price, stock):
    cur = _execute(
        "INSERT INTO menu_items (shop_id, name, category, price, stock) VALUES (?, ?, ?, ?, ?)",
        (shop_id, name, category, price, stock),
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


def save_order(order_no, table_no, status, priority, total, items, customer_email="", shop_id=0):
    """items = list of {"menu_item_id", "quantity", "price"}. Returns created_at."""
    created_at = datetime.now().isoformat(timespec="seconds")
    with closing(get_connection()) as conn:
        with conn:                            # both inserts succeed or neither does
            cur = conn.execute(
                "INSERT INTO orders (order_no, table_no, status, priority, total, created_at, "
                "customer_email, shop_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (order_no, str(table_no), status, priority, total, created_at,
                 customer_email, shop_id),
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
        "SELECT id, order_no, table_no, status, priority, total, created_at, customer_email, "
        "shop_id FROM orders"
    )
    for order in orders:
        order["items"] = _query(
            "SELECT menu_item_id, quantity, price FROM order_items WHERE order_id=?",
            (order["id"],),
        )
    return orders


# ---------- ADMINS (the canteen manager) ----------

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
