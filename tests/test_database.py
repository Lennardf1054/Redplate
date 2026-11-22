import os
import sqlite3
import tempfile

from Back_End import database as db


def expect_error(error, func, *args):
    try:
        func(*args)
    except error:
        return
    raise AssertionError(f"{func.__name__}{args} did not raise {error.__name__}")


def test_database():
    with tempfile.TemporaryDirectory() as folder:       # throwaway database file
        db.use_database(os.path.join(folder, "test.db"))
        db.create_tables()
        db.create_tables()                              # running twice is safe

        # menu
        assert db.load_menu_items() == []
        db.seed_sample_data()
        count = len(db.load_menu_items())
        assert count > 0
        db.seed_sample_data()                           # no duplicates
        assert len(db.load_menu_items()) == count
        new_id = db.add_menu_item("Halo-Halo", "Snacks", 45, 8)
        db.update_stock(new_id, 3)
        assert [m for m in db.load_menu_items() if m["id"] == new_id][0]["stock"] == 3
        expect_error(sqlite3.IntegrityError, db.add_menu_item, "Bad", "Meals", -5, 1)
        expect_error(sqlite3.IntegrityError, db.add_menu_item, "Bad", "Meals", 5, -1)
        expect_error(KeyError, db.update_stock, 9999, 1)

        # orders
        assert db.get_max_order_no() == 0
        items = [
            {"menu_item_id": 1, "quantity": 2, "price": 60},
            {"menu_item_id": 2, "quantity": 1, "price": 35},
        ]
        db.save_order(1, 5, "Pending", 0, 155, items)
        assert db.get_max_order_no() == 1
        orders = db.load_orders()
        assert len(orders) == 1 and len(orders[0]["items"]) == 2
        assert orders[0]["customer_email"] == ""        # no owner given
        db.save_order(2, 6, "Pending", 1, 60, items[:1], "juan@g.batstate-u.edu.ph")
        assert db.load_orders()[1]["customer_email"] == "juan@g.batstate-u.edu.ph"
        db.update_order_status(1, "Ready")
        assert db.load_orders()[0]["status"] == "Ready"
        expect_error(KeyError, db.update_order_status, 99, "Ready")
        expect_error(sqlite3.IntegrityError, db.save_order, 1, 2, "Pending", 0, 20, items)
        assert len(db.load_orders()) == 2               # failed save left nothing behind

        # admins
        db.add_admin("admin", "fakehash")
        assert db.get_admin("admin")["password_hash"] == "fakehash"
        assert db.get_admin("nobody") is None
        expect_error(sqlite3.IntegrityError, db.add_admin, "admin", "other")


def test_upgrade_old_database():
    """A database made before the customer_email column existed must be upgraded."""
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "old.db")
        conn = sqlite3.connect(path)
        conn.executescript("""
            CREATE TABLE menu_items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                category TEXT NOT NULL, price REAL NOT NULL, stock INTEGER NOT NULL,
                is_available INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, order_no INTEGER NOT NULL UNIQUE,
                table_no TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Pending',
                priority INTEGER NOT NULL DEFAULT 0, total REAL NOT NULL, created_at TEXT NOT NULL);
            INSERT INTO orders (order_no, table_no, status, priority, total, created_at)
                VALUES (7, '3', 'Completed', 1, 60, '2026-01-01T10:00:00');
        """)
        conn.commit()
        conn.close()
        db.use_database(path)
        db.create_tables()                              # adds the missing column
        orders = db.load_orders()
        assert orders[0]["order_no"] == 7 and orders[0]["customer_email"] == ""


if __name__ == "__main__":
    test_database()
    test_upgrade_old_database()
    print("All database tests passed")
