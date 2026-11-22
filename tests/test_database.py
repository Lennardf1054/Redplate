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

        # shops: each one is also a login account
        assert db.load_shops() == []
        shop_a = db.add_shop("Shop A", "hash-a")
        shop_b = db.add_shop("Shop B", "hash-b")
        assert [s["name"] for s in db.load_shops()] == ["Shop A", "Shop B"]
        expect_error(sqlite3.IntegrityError, db.add_shop, "shop a", "x")      # same name, any case
        db.update_shop_password(shop_a, "new-hash")
        assert [s for s in db.load_shops() if s["id"] == shop_a][0]["password_hash"] == "new-hash"
        expect_error(KeyError, db.update_shop_password, 999, "x")

        # menu: every item belongs to a shop
        assert db.load_menu_items() == []
        item_a = db.add_menu_item(shop_a, "Adobo", "Meals", 60, 10)
        item_b = db.add_menu_item(shop_b, "Iced Tea", "Drinks", 20, 5)
        items = {m["id"]: m for m in db.load_menu_items()}
        assert items[item_a]["shop_id"] == shop_a and items[item_b]["shop_id"] == shop_b
        db.update_stock(item_a, 3)
        assert {m["id"]: m for m in db.load_menu_items()}[item_a]["stock"] == 3
        expect_error(sqlite3.IntegrityError, db.add_menu_item, shop_a, "Bad", "Meals", -5, 1)
        expect_error(sqlite3.IntegrityError, db.add_menu_item, shop_a, "Bad", "Meals", 5, -1)
        expect_error(KeyError, db.update_stock, 9999, 1)

        # orders
        assert db.get_max_order_no() == 0
        lines = [{"menu_item_id": item_a, "quantity": 2, "price": 60}]
        db.save_order(1, 5, "Pending", 0, 120, lines)
        assert db.get_max_order_no() == 1
        orders = db.load_orders()
        assert len(orders) == 1 and len(orders[0]["items"]) == 1
        assert orders[0]["customer_email"] == "" and orders[0]["shop_id"] == 0
        db.save_order(2, 6, "Pending", 1, 60, lines[:1], "juan@g.batstate-u.edu.ph", shop_a)
        saved = db.load_orders()[1]
        assert saved["customer_email"] == "juan@g.batstate-u.edu.ph" and saved["shop_id"] == shop_a
        db.update_order_status(1, "Ready")
        assert db.load_orders()[0]["status"] == "Ready"
        expect_error(KeyError, db.update_order_status, 99, "Ready")
        expect_error(sqlite3.IntegrityError, db.save_order, 1, 2, "Pending", 0, 20, lines)
        assert len(db.load_orders()) == 2               # failed save left nothing behind

        # old rows without a shop can be handed to one
        assert db.has_unassigned_rows()                 # order 1 was saved without a shop
        db.assign_unassigned_rows(shop_b)
        assert not db.has_unassigned_rows() and db.load_orders()[0]["shop_id"] == shop_b

        # the canteen manager
        db.add_admin("admin", "fakehash")
        assert db.get_admin("admin")["password_hash"] == "fakehash"
        assert db.get_admin("nobody") is None
        expect_error(sqlite3.IntegrityError, db.add_admin, "admin", "other")


def test_upgrade_old_database():
    """A database made before shops and customer emails existed must be upgraded."""
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
            INSERT INTO menu_items (name, category, price, stock) VALUES ('Old Item', 'Meals', 50, 4);
            INSERT INTO orders (order_no, table_no, status, priority, total, created_at)
                VALUES (7, '3', 'Completed', 1, 60, '2026-01-01T10:00:00');
        """)
        conn.commit()
        conn.close()
        db.use_database(path)
        db.create_tables()                              # adds the missing columns
        orders = db.load_orders()
        assert orders[0]["order_no"] == 7 and orders[0]["customer_email"] == "" and orders[0]["shop_id"] == 0
        assert db.load_menu_items()[0]["shop_id"] == 0
        assert db.has_unassigned_rows()


if __name__ == "__main__":
    test_database()
    test_upgrade_old_database()
    print("All database tests passed")
