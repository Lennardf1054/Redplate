import os
import sqlite3
import tempfile

import config
from Back_End import database as db
from Back_End import service


def expect_error(error, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except error:
        return
    raise AssertionError(f"{func.__name__}{args} did not raise {error.__name__}")


def shop_id(name):
    return [s["id"] for s in service.list_shops() if s["name"] == name][0]


def test_service():
    with tempfile.TemporaryDirectory() as folder:
        db.use_database(os.path.join(folder, "test.db"))
        service.init()
        domain = config.ALLOWED_EMAIL_DOMAIN
        me = "juan@" + domain
        ana = "ana@" + domain

        # canteen manager login and student emails
        assert service.check_admin("admin", "admin123")
        assert not service.check_admin("admin", "wrong")
        assert not service.check_admin("nobody", "admin123")
        assert service.check_student_email("  Juan.Cruz@" + domain.upper() + " ") == "juan.cruz@" + domain
        for bad in ("juan@gmail.com", "@" + domain, "", "a@b@" + domain,
                    "juan@" + domain + ".evil.com", "juan smith@" + domain, "juan@x" + domain):
            expect_error(ValueError, service.check_student_email, bad)

        # the sample shops, each with its own login
        names = [s["name"] for s in service.list_shops()]
        assert names == sorted(names) and "Mang Tomas Kitchen" in names and "Sip and Snack" in names
        A = shop_id("Mang Tomas Kitchen")
        B = shop_id("Sip and Snack")
        assert service.check_shop_login(A, config.DEFAULT_SHOP_PASSWORD)
        assert not service.check_shop_login(A, "wrong")
        assert not service.check_shop_login(999, config.DEFAULT_SHOP_PASSWORD)
        assert service.get_shop(A)["name"] == "Mang Tomas Kitchen" and "password_hash" not in service.get_shop(A)
        expect_error(ValueError, service.get_shop, 999)
        cards = {c["name"]: c["item_count"] for c in service.shop_cards()}
        assert cards["Mang Tomas Kitchen"] == 3 and cards["Sip and Snack"] == 2   # Iced Tea has no stock

        # each shop has its own menu
        assert [m["name"] for m in service.get_menu(A, search="adobo")] == ["Chicken Adobo"]
        assert service.get_menu(B, search="adobo") == []
        prices = [m["price"] for m in service.get_menu(A, sort_by="price")]
        assert prices == sorted(prices)          # built-in sorted() only checks the result
        assert service.get_menu(A, search="zzz") == []
        adobo, pancit, rice = [m["id"] for m in service.get_menu(A)]                # sorted by name
        tea = [m["id"] for m in service.get_menu(B, search="iced")][0]
        banana = [m["id"] for m in service.get_menu(B, search="banana")][0]

        # cart: add, undo, invalid. One cart per student per shop.
        service.cart_add(me, A, adobo)
        service.cart_add(me, A, adobo)
        lines, total = service.cart_view(me, A)
        assert lines[0]["qty"] == 2 and total == 120
        assert service.cart_view(me, B) == ([], 0)                 # the other shop's cart is separate
        assert service.cart_view(ana, A) == ([], 0)                # and so is another student's
        service.cart_undo(me, A)
        assert service.cart_view(me, A)[1] == 60
        service.cart_undo(me, A)
        assert service.cart_view(me, A) == ([], 0)
        expect_error(ValueError, service.cart_undo, me, A)         # nothing to undo
        expect_error(ValueError, service.cart_add, me, A, tea)     # that item belongs to shop B
        expect_error(ValueError, service.cart_add, me, B, tea)     # out of stock
        expect_error(ValueError, service.cart_add, me, A, 999)     # no such item
        expect_error(ValueError, service.cart_remove, me, A, adobo)   # not in cart
        for _ in range(5):                                         # Pancit has stock 5
            service.cart_add(me, A, pancit)
        expect_error(ValueError, service.cart_add, me, A, pancit)  # over stock

        # placing orders: invalid input
        expect_error(ValueError, service.place_order, "nobody@" + domain, A, "5")
        expect_error(ValueError, service.place_order, me, A, "0")
        expect_error(ValueError, service.place_order, me, A, "abc")
        expect_error(ValueError, service.place_order, me, A, "51")
        expect_error(ValueError, service.place_order, me, 999, "5")
        expect_error(ValueError, service.place_order, me, B, "5")  # empty cart in shop B

        # placing orders: normal, urgent, and in two shops
        assert service.place_order(me, A, "5") == 1
        assert service.cart_view(me, A) == ([], 0)                 # cart cleared
        assert service.find_order(1)["total"] == 175
        assert service.find_order(1)["items_text"] == "5x Pancit Canton"
        assert service.find_order(1)["shop_name"] == "Mang Tomas Kitchen"
        assert [m for m in service.get_menu(A) if m["id"] == pancit][0]["stock"] == 0
        service.cart_add(ana, A, adobo)
        assert service.place_order(ana, A, "7", urgent=True) == 2
        service.cart_add(me, A, rice)
        assert service.place_order(me, A, "2") == 3
        service.cart_add(me, B, banana)
        assert service.place_order(me, B, "1") == 4

        next_a, active_a = service.dashboard(A)
        assert next_a["order_no"] == 2                             # urgent jumps the line in shop A
        assert [o["order_no"] for o in active_a] == [1, 2, 3]
        next_b, active_b = service.dashboard(B)
        assert next_b["order_no"] == 4 and [o["order_no"] for o in active_b] == [4]
        assert [o["order_no"] for o in service.all_orders(B)] == [4]
        assert service.find_shop_order(A, 4) is None and service.find_shop_order(B, 4) is not None

        # status changes, the line moving, and shops cannot touch each other's orders
        expect_error(ValueError, service.update_status, B, 3, "Preparing")     # order 3 is shop A's
        expect_error(ValueError, service.update_status, A, 4, "Preparing")     # order 4 is shop B's
        service.update_status(A, 2, "Preparing")
        assert service.dashboard(A)[0]["order_no"] == 1            # back to first come first served
        assert service.dashboard(B)[0]["order_no"] == 4            # shop B was not affected
        service.update_status(A, 1, "Preparing")
        assert service.dashboard(A)[0]["order_no"] == 3
        expect_error(ValueError, service.update_status, A, 3, "Ready")         # skips a step
        expect_error(ValueError, service.update_status, A, 3, "Nope")
        expect_error(ValueError, service.update_status, A, 99, "Preparing")
        service.update_status(A, 1, "Ready")
        service.update_status(A, 1, "Completed")
        assert service.find_order(99) is None

        # sales report: one shop at a time
        completed, total_sales, used = service.sales_report(A, "total")
        assert [o["order_no"] for o in completed] == [1] and total_sales == 175
        assert service.sales_report(B) == ([], 0, "order_no")
        assert service.sales_report(A, "bad")[2] == "order_no"

        # a student's orders, newest first, from every shop
        assert [o["order_no"] for o in service.my_orders(me)] == [4, 3, 1]
        assert [o["order_no"] for o in service.my_orders(me, limit=2)] == [4, 3]
        assert [o["order_no"] for o in service.my_orders(ana)] == [2]
        assert service.my_orders("maria@" + domain) == []

        # restart: everything must come back from the database
        service.init()
        assert service.find_order(2)["status"] == "Preparing"
        assert service.find_order(3)["order_no"] == 3              # sorted list rebuilt from the BST
        assert service.dashboard(A)[0]["order_no"] == 3
        assert service.dashboard(B)[0]["order_no"] == 4
        assert [o["order_no"] for o in service.my_orders(me)] == [4, 3, 1]
        service.cart_add(me, A, adobo)
        assert service.place_order(me, A, "1") == 5                # numbering continues
        assert service.find_order(5)["order_no"] == 5              # new order added to the list

        # a deleted item must not break a cart that holds it
        temp_id = service.add_menu_item(A, "Temp Item", "Snacks", "10", "5")
        service.cart_add(ana, A, temp_id)
        expect_error(ValueError, service.remove_menu_item, B, temp_id)   # shop B cannot delete it
        assert service.remove_menu_item(A, temp_id) == "deleted"
        assert service.cart_view(ana, A) == ([], 0)

        # menu management stays inside one shop
        new_id = service.add_menu_item(A, "Halo-Halo Special", "Snacks", "45", "8")
        expect_error(ValueError, service.add_menu_item, A, "", "Meals", "10", "1")
        expect_error(ValueError, service.add_menu_item, A, "X", "Meals", "-5", "1")
        expect_error(ValueError, service.add_menu_item, A, "X", "Meals", "abc", "1")
        expect_error(ValueError, service.add_menu_item, A, "X", "Meals", "10", "1.5")
        expect_error(ValueError, service.add_menu_item, 999, "X", "Meals", "10", "1")
        expect_error(ValueError, service.update_menu_item, B, new_id, "Hacked", "Meals", "1", "1")
        service.update_menu_item(A, new_id, "Halo-Halo Deluxe", "Snacks", "50", "6")
        assert "Halo-Halo Deluxe" in [m["name"] for m in service.get_menu(A)]
        assert "Halo-Halo Deluxe" not in [m["name"] for m in service.get_menu(B)]
        assert service.remove_menu_item(A, new_id) == "deleted"
        assert service.remove_menu_item(A, adobo) == "hidden"      # old orders use it
        assert adobo not in [m["id"] for m in service.get_menu(A)]
        assert adobo in [m["id"] for m in service.get_menu(A, include_hidden=True)]
        item = [m for m in service.get_menu(A, include_hidden=True) if m["id"] == adobo][0]
        service.update_menu_item(A, adobo, item["name"], item["category"], item["price"],
                                 item["stock"], available=True)    # bring it back
        assert adobo in [m["id"] for m in service.get_menu(A)]
        expect_error(ValueError, service.remove_menu_item, A, 999)

        # the manager adds a shop: its login is created at the same time
        new_shop = service.add_shop("  Rice   Bowl ", "ricebowl1")
        assert service.get_shop(new_shop)["name"] == "Rice Bowl"            # spaces tidied
        assert "Rice Bowl" in [s["name"] for s in service.list_shops()]
        assert service.check_shop_login(new_shop, "ricebowl1")
        assert not service.check_shop_login(new_shop, "ricebowl2")
        assert not service.check_shop_login(new_shop, config.DEFAULT_SHOP_PASSWORD)
        assert service.get_menu(new_shop) == [] and service.dashboard(new_shop) == (None, [])
        expect_error(ValueError, service.add_shop, "rice bowl", "another1")   # same name, any case
        expect_error(ValueError, service.add_shop, "R", "ricebowl1")          # name too short
        expect_error(ValueError, service.add_shop, "Short Pass", "12345")     # password too short
        service.add_menu_item(new_shop, "Rice Meal", "Meals", "55", "10")
        service.cart_add(ana, new_shop, service.get_menu(new_shop)[0]["id"])
        assert service.place_order(ana, new_shop, "3") == 6                   # the new shop takes orders
        assert service.dashboard(new_shop)[0]["order_no"] == 6
        service.reset_shop_password(new_shop, "newsecret9")
        assert service.check_shop_login(new_shop, "newsecret9") and not service.check_shop_login(new_shop, "ricebowl1")
        expect_error(ValueError, service.reset_shop_password, new_shop, "abc")
        expect_error(ValueError, service.reset_shop_password, 999, "newsecret9")
        service.init()                                             # the new shop survives a restart
        assert service.check_shop_login(new_shop, "newsecret9")
        assert service.dashboard(new_shop)[0]["order_no"] == 6


def test_adopts_old_one_shop_data():
    """Data from the version without shops moves into a 'Main Canteen' shop."""
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
            CREATE TABLE order_items (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL,
                menu_item_id INTEGER NOT NULL, quantity INTEGER NOT NULL, price REAL NOT NULL);
            INSERT INTO menu_items (name, category, price, stock) VALUES ('Old Adobo', 'Meals', 60, 4);
            INSERT INTO orders (order_no, table_no, status, priority, total, created_at)
                VALUES (7, '3', 'Completed', 1, 60, '2026-01-01T10:00:00');
            INSERT INTO order_items (order_id, menu_item_id, quantity, price) VALUES (1, 1, 1, 60);
        """)
        conn.commit()
        conn.close()
        db.use_database(path)
        service.init()
        shops = service.list_shops()
        assert [s["name"] for s in shops] == ["Main Canteen"]          # no sample shops added
        main = shops[0]["id"]
        assert service.check_shop_login(main, config.DEFAULT_SHOP_PASSWORD)
        assert [m["name"] for m in service.get_menu(main)] == ["Old Adobo"]
        assert service.find_order(7)["shop_name"] == "Main Canteen"
        assert service.sales_report(main)[1] == 60


if __name__ == "__main__":
    test_service()
    test_adopts_old_one_shop_data()
    print("All service tests passed")
