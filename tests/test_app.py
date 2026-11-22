"""Web-level test: drives the whole site with Flask's test client (no browser needed).
Run from the Redplate folder:  python -m tests.test_app
"""
import os
import tempfile

from Back_End import database as db


def page(response):
    return response.get_data(as_text=True)


def test_app():
    with tempfile.TemporaryDirectory() as folder:
        db.use_database(os.path.join(folder, "test.db"))     # never touch the real database
        import app as app_module                             # app.py loads the data on import
        client = app_module.app.test_client()

        # ---- customer side ----
        response = client.get("/")
        assert response.status_code == 302 and response.headers["Location"].endswith("/menu")
        html = page(client.get("/menu"))
        assert "Chicken Adobo" in html and "Pancit Canton" in html
        html = page(client.get("/menu?q=adobo"))
        assert "Chicken Adobo" in html and "Pancit Canton" not in html
        assert client.get("/menu?sort=hacker").status_code == 200            # bad sort is ignored

        client.post("/cart/add/1")
        html = page(client.get("/cart"))
        assert "Chicken Adobo" in html and "Total" in html
        html = page(client.post("/cart/add/3", follow_redirects=True))       # out of stock
        assert "out of stock" in html
        client.post("/cart/undo")
        assert "Your cart is empty" in page(client.get("/cart"))
        assert "Nothing to undo" in page(client.post("/cart/undo", follow_redirects=True))

        client.post("/cart/add/1")
        html = page(client.post("/checkout", data={"table_no": "0"}, follow_redirects=True))
        assert "Table number must be" in html
        html = page(client.post("/checkout", data={"table_no": "abc"}, follow_redirects=True))
        assert "Table number must be" in html
        response = client.post("/checkout", data={"table_no": "5", "urgent": "on"})
        assert response.status_code == 302 and response.headers["Location"].endswith("/order/1")
        html = page(client.get("/order/1"))
        assert "Order #1" in html and 'step active">Pending' in html
        assert client.get("/order/999").status_code == 404
        assert client.get("/nope").status_code == 404

        # ---- admin side is protected ----
        for url in ("/admin/dashboard", "/admin/orders", "/admin/menu", "/admin/reports",
                    "/admin/dashboard/live"):
            response = client.get(url)
            assert response.status_code == 302 and "/admin/login" in response.headers["Location"]
        assert client.post("/admin/orders/1/status", data={"status": "Preparing"}).status_code == 302
        assert "Wrong username or password" in page(
            client.post("/admin/login", data={"username": "admin", "password": "nope"},
                        follow_redirects=True))
        response = client.post("/admin/login", data={"username": "admin", "password": "admin123"})
        assert response.status_code == 302 and response.headers["Location"].endswith("/admin/dashboard")

        # ---- admin: dashboard and status ----
        html = page(client.get("/admin/dashboard"))
        assert "Next to serve" in html and "#1" in html and "URGENT" in html
        assert "5x" not in html and "1x Chicken Adobo" in html               # items text, not a method
        assert "Mark Preparing" in page(client.get("/admin/dashboard/live"))
        assert "Cannot change" in page(client.post(
            "/admin/orders/1/status", data={"status": "Completed"}, follow_redirects=True))
        client.post("/admin/orders/1/status", data={"status": "Preparing"})
        assert 'step active">Preparing' in page(client.get("/order/1/live"))  # customer sees it
        client.post("/admin/orders/1/status", data={"status": "Ready"})
        client.post("/admin/orders/1/status", data={"status": "Completed"})

        # ---- admin: all orders and search ----
        html = page(client.get("/admin/orders"))
        assert "1x Chicken Adobo" in html and "built-in method" not in html
        assert "1x Chicken Adobo" in page(client.get("/admin/orders?order_id=1"))
        assert "No order found" in page(client.get("/admin/orders?order_id=999"))
        assert "valid order number" in page(client.get("/admin/orders?order_id=abc"))
        assert "valid order number" in page(client.get("/admin/orders?order_id=99999999999"))

        # ---- admin: report ----
        html = page(client.get("/admin/reports?sort=total"))
        assert "Total sales" in html and "₱60" in html and "built-in method" not in html
        assert client.get("/admin/reports?sort=hacker").status_code == 200

        # ---- admin: menu management ----
        assert "Chicken Adobo" in page(client.get("/admin/menu"))
        assert "Item added" in page(client.post(
            "/admin/menu", data={"name": "Halo-Halo", "category": "Snacks", "price": "45", "stock": "8"},
            follow_redirects=True))
        assert "Price must be greater than 0" in page(client.post(
            "/admin/menu", data={"name": "X", "category": "Meals", "price": "-1", "stock": "1"},
            follow_redirects=True))
        fields = {"name": "Chicken Adobo", "category": "Meals", "price": "60", "stock": "9"}
        client.post("/admin/menu/1/update", data=fields)                     # no 'available' = hide
        assert "Chicken Adobo" not in page(client.get("/menu"))
        client.post("/admin/menu/1/update", data={**fields, "available": "on"})
        assert "Chicken Adobo" in page(client.get("/menu"))
        assert "hidden from customers" in page(client.post("/admin/menu/1/delete",
                                                           follow_redirects=True))
        assert "Item deleted" in page(client.post("/admin/menu/5/delete", follow_redirects=True))

        # ---- logout ----
        client.get("/admin/logout")
        assert client.get("/admin/dashboard").status_code == 302


if __name__ == "__main__":
    test_app()
    print("All web tests passed")
