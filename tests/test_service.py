import os
import tempfile

from Back_End import database as db
from Back_End import service


def expect_error(error, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except error:
        return
    raise AssertionError(f"{func.__name__}{args} did not raise {error.__name__}")


def test_service():
    with tempfile.TemporaryDirectory() as folder:
        db.use_database(os.path.join(folder, "test.db"))
        service.init()

        # menu: search and sort
        assert "Chicken Adobo" in [m["name"] for m in service.get_menu()]
        assert [m["name"] for m in service.get_menu(search="adobo")] == ["Chicken Adobo"]
        prices = [m["price"] for m in service.get_menu(sort_by="price")]
        assert prices == sorted(prices)          # built-in sorted() only checks the result
        assert service.get_menu(search="zzz") == []

        # cart: add, undo, invalid
        service.cart_add("s1", 1)
        service.cart_add("s1", 1)
        lines, total = service.cart_view("s1")
        assert lines[0]["qty"] == 2 and total == 120
        service.cart_undo("s1")
        assert service.cart_view("s1")[1] == 60
        service.cart_undo("s1")
        assert service.cart_view("s1") == ([], 0)
        expect_error(ValueError, service.cart_undo, "s1")          # nothing to undo
        expect_error(ValueError, service.cart_add, "s1", 3)        # out of stock
        expect_error(ValueError, service.cart_add, "s1", 999)      # no such item
        expect_error(ValueError, service.cart_remove, "s1", 1)     # not in cart
        for _ in range(5):                                         # item 2 has stock 5
            service.cart_add("s1", 2)
        expect_error(ValueError, service.cart_add, "s1", 2)        # over stock

        # placing orders: invalid input
        expect_error(ValueError, service.place_order, "nobody", "5")
        expect_error(ValueError, service.place_order, "s1", "0")
        expect_error(ValueError, service.place_order, "s1", "abc")
        expect_error(ValueError, service.place_order, "s1", "51")

        # placing orders: normal and urgent
        assert service.place_order("s1", "5") == 1
        assert service.cart_view("s1") == ([], 0)                  # cart cleared
        assert service.find_order(1)["total"] == 175
        assert [m for m in service.get_menu() if m["id"] == 2][0]["stock"] == 0
        service.cart_add("s2", 1)
        assert service.place_order("s2", "7", urgent=True) == 2
        service.cart_add("s3", 4)
        assert service.place_order("s3", "2") == 3

        next_order, active = service.dashboard()
        assert next_order["order_no"] == 2                         # urgent jumps the line
        assert len(active) == 3

        # status changes and the line moving
        service.update_status(2, "Preparing")
        assert service.dashboard()[0]["order_no"] == 1             # back to first come first served
        service.update_status(1, "Preparing")
        assert service.dashboard()[0]["order_no"] == 3
        expect_error(ValueError, service.update_status, 3, "Ready")      # skips a step
        expect_error(ValueError, service.update_status, 3, "Nope")
        expect_error(ValueError, service.update_status, 99, "Preparing")
        service.update_status(1, "Ready")
        service.update_status(1, "Completed")
        assert service.find_order(99) is None

        # sales report
        completed, total_sales, used = service.sales_report("total")
        assert [o["order_no"] for o in completed] == [1] and total_sales == 175
        assert service.sales_report("bad")[2] == "order_no"

        # restart: everything must come back from the database
        service.init()
        assert service.find_order(2)["status"] == "Preparing"
        assert service.dashboard()[0]["order_no"] == 3
        service.cart_add("s4", 1)
        assert service.place_order("s4", "1") == 4                 # numbering continues

        # menu management
        new_id = service.add_menu_item("Halo-Halo", "Snacks", "45", "8")
        expect_error(ValueError, service.add_menu_item, "", "Meals", "10", "1")
        expect_error(ValueError, service.add_menu_item, "X", "Meals", "-5", "1")
        expect_error(ValueError, service.add_menu_item, "X", "Meals", "abc", "1")
        expect_error(ValueError, service.add_menu_item, "X", "Meals", "10", "1.5")
        service.update_menu_item(new_id, "Halo-Halo Special", "Snacks", "50", "6")
        assert service.remove_menu_item(new_id) == "deleted"
        assert service.remove_menu_item(1) == "hidden"             # old orders use it
        assert 1 not in [m["id"] for m in service.get_menu()]
        assert 1 in [m["id"] for m in service.get_menu(include_hidden=True)]
        expect_error(ValueError, service.remove_menu_item, 999)


if __name__ == "__main__":
    test_service()
    print("All service tests passed")