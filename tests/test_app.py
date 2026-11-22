"""Web-level test: drives the whole site with Flask's test client (no browser, no internet).
Run from the Redplate folder:  python -m tests.test_app
"""
import os
import tempfile

import config
from Back_End import database as db

AJAX = {"X-Requested-With": "fetch"}


def page(response):
    return response.get_data(as_text=True)


def test_app():
    # Pretend Google is set up, and that demo sign-in is on, whatever the real settings are.
    config.GOOGLE_ENABLED = True
    config.GOOGLE_CLIENT_ID = "test-client"
    config.GOOGLE_CLIENT_SECRET = "test-secret"
    config.GOOGLE_REDIRECT_URI = ""
    config.DEMO_LOGIN = True
    domain = config.ALLOWED_EMAIL_DOMAIN
    shop_password = config.DEFAULT_SHOP_PASSWORD

    with tempfile.TemporaryDirectory() as folder:
        db.use_database(os.path.join(folder, "test.db"))     # never touch the real database
        import app as app_module                             # app.py loads the data on import
        from Back_End.routes import auth
        flask_app = app_module.app
        juan = flask_app.test_client()

        # ---- not signed in: everything customer-side sends you to the login page ----
        for method, url in (("get", "/"), ("get", "/shops"), ("get", "/shop/1"), ("get", "/menu"),
                            ("get", "/my-orders"), ("get", "/order/1"), ("get", "/shop/1/orders-box"),
                            ("post", "/shop/1/cart/add/1"), ("post", "/shop/1/checkout")):
            response = getattr(juan, method)(url)
            assert response.status_code == 302 and response.headers["Location"].endswith("/login"), url
        html = page(juan.get("/login"))
        assert "Sign in with Google" in html and "Demo mode" in html

        # ---- demo sign-in: only school accounts ----
        assert "Please use your school Google account" in page(
            juan.post("/auth/demo", data={"email": "juan@gmail.com"}, follow_redirects=True))
        response = juan.post("/auth/demo", data={"email": "juan@" + domain})
        assert response.status_code == 302 and response.headers["Location"].endswith("/shops")
        assert juan.get("/login").status_code == 302                         # already signed in
        assert juan.get("/").headers["Location"].endswith("/shops")
        assert juan.get("/menu").headers["Location"].endswith("/shops")

        # ---- the shops page ----
        html = page(juan.get("/shops"))
        assert "Mang Tomas Kitchen" in html and "Sip and Snack" in html and "My Orders" in html
        assert juan.get("/shop/999").status_code == 404

        # ---- a shop page: menu on the left, cart and orders in the sidebar ----
        html = page(juan.get("/shop/1"))
        assert "Chicken Adobo" in html and "Plain Rice" in html and "Halo-Halo" not in html
        assert "Your cart" in html and "My orders" in html and "data-cart-box" in html
        assert "Halo-Halo" in page(juan.get("/shop/2"))
        html = page(juan.get("/shop/1?q=adobo"))
        assert "Chicken Adobo" in html and "Pancit Canton" not in html
        assert juan.get("/shop/1?sort=hacker").status_code == 200            # bad sort is ignored

        # adding to the cart without JavaScript: normal redirect back to the shop
        response = juan.post("/shop/1/cart/add/1")
        assert response.status_code == 302 and response.headers["Location"].endswith("/shop/1")
        assert "Chicken Adobo" in page(juan.get("/shop/1"))
        # with JavaScript: only the cart box comes back, with the new quantity
        box = page(juan.post("/shop/1/cart/add/1", headers=AJAX))
        assert "<html" not in box and "Chicken Adobo" in box and "Total: ₱120" in box
        assert "Total: ₱60" in page(juan.post("/shop/1/cart/decrease/1", headers=AJAX))
        assert "Total: ₱120" in page(juan.post("/shop/1/cart/add/1", headers=AJAX))
        assert "Your cart is empty" in page(juan.post("/shop/1/cart/remove/1", headers=AJAX))
        assert "Total: ₱120" in page(juan.post("/shop/1/cart/undo", headers=AJAX))        # undo the remove
        assert "Nothing to undo" in page(juan.post("/shop/2/cart/undo", headers=AJAX))
        assert "does not exist" in page(juan.post("/shop/1/cart/add/4", headers=AJAX))      # item of shop 2
        assert "out of stock" in page(juan.post("/shop/2/cart/add/4", headers=AJAX))
        assert juan.post("/shop/999/cart/add/1", headers=AJAX).status_code == 404
        assert "Your cart is empty" in page(juan.get("/shop/2"))              # carts are per shop

        # ---- checkout ----
        assert "Table number must be" in page(
            juan.post("/shop/1/checkout", data={"table_no": "0"}, headers=AJAX))
        assert "Table number must be" in page(
            juan.post("/shop/1/checkout", data={"table_no": "abc"}, headers=AJAX))
        box = page(juan.post("/shop/1/checkout", data={"table_no": "5", "urgent": "on"}, headers=AJAX))
        assert "Order #1 placed" in box and "Your cart is empty" in box
        orders = page(juan.get("/shop/1/orders-box"))
        assert "#1" in orders and "Pending" in orders and "Mang Tomas Kitchen" in orders
        assert "#1" in page(juan.get("/shop/2"))                              # sidebar shows every shop's orders
        html = page(juan.get("/order/1"))
        assert "Order #1" in html and "Mang Tomas Kitchen" in html and 'step active">Pending' in html
        juan.post("/shop/2/cart/add/5", headers=AJAX)                          # Fried Banana
        response = juan.post("/shop/2/checkout", data={"table_no": "6"})       # no JavaScript
        assert response.status_code == 302 and response.headers["Location"].endswith("/shop/2")
        assert "Order #2 placed" in page(juan.get("/shop/2"))
        html = page(juan.get("/my-orders"))
        assert "Mang Tomas Kitchen" in html and "Sip and Snack" in html
        assert juan.get("/order/999").status_code == 404
        assert juan.get("/nope").status_code == 404

        # ---- another student cannot see Juan's orders ----
        maria = flask_app.test_client()
        maria.post("/auth/demo", data={"email": "maria@" + domain})
        assert maria.get("/order/1").status_code == 404
        assert maria.get("/order/1/live").status_code == 404
        assert "no orders yet" in page(maria.get("/my-orders"))
        assert "#1" not in page(maria.get("/shop/1/orders-box"))
        maria.post("/shop/1/cart/add/1", headers=AJAX)
        assert "Chicken Adobo" in page(maria.get("/shop/1"))                  # her own cart
        assert "Your cart is empty" in page(juan.get("/shop/1"))              # and Juan's is separate

        # ---- sign in with Google (Google's servers are replaced by fakes) ----
        pedro = flask_app.test_client()
        response = pedro.get("/auth/google")
        location = response.headers["Location"]
        assert response.status_code == 302 and location.startswith("https://accounts.google.com/")
        assert "client_id=test-client" in location and "scope=openid+email" in location
        with pedro.session_transaction() as session:
            state = session["oauth_state"]
        auth._post_form = lambda url, data: {"access_token": "token"}
        auth._get_json = lambda url, token: {"email": "pedro@" + domain, "email_verified": True}
        response = pedro.get("/auth/google/callback?code=abc&state=" + state)
        assert response.status_code == 302 and response.headers["Location"].endswith("/shops")
        assert pedro.get("/shops").status_code == 200

        def google_attempt(post_form, get_json, give_state=True, extra=""):
            client = flask_app.test_client()
            client.get("/auth/google")
            with client.session_transaction() as session:
                real_state = session["oauth_state"]
            auth._post_form, auth._get_json = post_form, get_json
            sent = real_state if give_state else "forged"
            html = page(client.get(f"/auth/google/callback?code=abc&state={sent}{extra}",
                                   follow_redirects=True))
            with client.session_transaction() as session:
                assert "student" not in session                             # nobody got in
            return html

        ok_token = lambda url, data: {"access_token": "token"}
        assert "could not be verified" in google_attempt(
            ok_token, lambda u, t: {"email": "x@" + domain, "email_verified": True}, give_state=False)
        assert "cancelled" in google_attempt(ok_token, lambda u, t: {}, extra="&error=access_denied")
        assert "school Google account" in google_attempt(
            ok_token, lambda u, t: {"email": "pedro@gmail.com", "email_verified": True})
        assert "not verified" in google_attempt(
            ok_token, lambda u, t: {"email": "pedro@" + domain, "email_verified": False})

        def no_internet(*args):
            raise OSError("no internet")
        assert "Could not sign in" in google_attempt(no_internet, no_internet)
        assert "Could not sign in" in google_attempt(lambda u, d: {}, lambda u, t: {})

        config.DEMO_LOGIN = False                                           # demo sign-in can be turned off
        assert "turned off" in page(flask_app.test_client().post(
            "/auth/demo", data={"email": "x@" + domain}, follow_redirects=True))
        config.DEMO_LOGIN = True

        # ---- staff login: every shop has its own password ----
        staff1 = flask_app.test_client()
        html = page(staff1.get("/admin/login"))
        assert "Mang Tomas Kitchen" in html and "Sip and Snack" in html and "Canteen manager" in html
        for url in ("/admin/dashboard", "/admin/orders", "/admin/menu", "/admin/reports",
                    "/admin/dashboard/live", "/admin/shops"):
            response = staff1.get(url)
            assert response.status_code == 302 and "/admin/login" in response.headers["Location"], url
        assert staff1.post("/admin/orders/1/status", data={"status": "Preparing"}).status_code == 302
        assert juan.get("/admin/dashboard").status_code == 302              # a student is not staff
        for account, password in (("1", "wrong"), ("2", "admin123"), ("999", shop_password),
                                  ("abc", shop_password), ("manager", shop_password), ("", "")):
            assert "Wrong shop or password" in page(staff1.post(
                "/admin/login", data={"account": account, "password": password}, follow_redirects=True))
        response = staff1.post("/admin/login", data={"account": "1", "password": shop_password})
        assert response.status_code == 302 and response.headers["Location"].endswith("/admin/dashboard")
        assert staff1.get("/admin/shops").status_code == 302               # only the manager adds shops

        # ---- shop 1 staff: dashboard and status ----
        html = page(staff1.get("/admin/dashboard"))
        assert "Next to serve" in html and "#1" in html and "URGENT" in html
        assert "2x Chicken Adobo" in html and "Mang Tomas Kitchen" in html
        assert "#2" not in html                                             # order 2 belongs to shop 2
        assert "Mark Preparing" in page(staff1.get("/admin/dashboard/live"))
        assert "Cannot change" in page(staff1.post(
            "/admin/orders/1/status", data={"status": "Completed"}, follow_redirects=True))
        staff1.post("/admin/orders/1/status", data={"status": "Preparing"})
        assert 'step active">Preparing' in page(juan.get("/order/1/live"))  # the student sees it
        assert "Preparing" in page(juan.get("/shop/2/orders-box"))          # and in the sidebar
        staff1.post("/admin/orders/1/status", data={"status": "Ready"})
        staff1.post("/admin/orders/1/status", data={"status": "Completed"})

        # ---- shop 2 staff cannot touch shop 1 ----
        staff2 = flask_app.test_client()
        response = staff2.post("/admin/login", data={"account": "2", "password": shop_password})
        assert response.headers["Location"].endswith("/admin/dashboard")
        html = page(staff2.get("/admin/dashboard"))
        assert "Sip and Snack" in html and "#2" in html and "#1" not in html
        assert "not found" in page(staff2.post(
            "/admin/orders/1/status", data={"status": "Preparing"}, follow_redirects=True))
        assert "No order found" in page(staff2.get("/admin/orders?order_id=1"))
        assert "Chicken Adobo" not in page(staff2.get("/admin/menu"))
        assert "does not exist" in page(staff2.post(
            "/admin/menu/1/update", data={"name": "Hacked", "category": "Meals", "price": "1", "stock": "1"},
            follow_redirects=True))
        assert "does not exist" in page(staff2.post("/admin/menu/1/delete", follow_redirects=True))
        assert "Hacked" not in page(juan.get("/shop/1"))
        assert "₱120" not in page(staff2.get("/admin/reports"))             # shop 1's sales stay private

        # ---- shop 1 staff: all orders, search, report, menu ----
        html = page(staff1.get("/admin/orders"))
        assert "2x Chicken Adobo" in html and "built-in method" not in html and "Fried Banana" not in html
        assert "2x Chicken Adobo" in page(staff1.get("/admin/orders?order_id=1"))
        assert "No order found" in page(staff1.get("/admin/orders?order_id=2"))        # shop 2's order
        assert "No order found" in page(staff1.get("/admin/orders?order_id=999"))
        assert "valid order number" in page(staff1.get("/admin/orders?order_id=abc"))
        assert "valid order number" in page(staff1.get("/admin/orders?order_id=99999999999"))
        html = page(staff1.get("/admin/reports?sort=total"))
        assert "Total sales" in html and "₱120" in html and "built-in method" not in html
        assert staff1.get("/admin/reports?sort=hacker").status_code == 200
        assert "Chicken Adobo" in page(staff1.get("/admin/menu"))
        assert "Item added" in page(staff1.post(
            "/admin/menu", data={"name": "Leche Flan", "category": "Snacks", "price": "30", "stock": "8"},
            follow_redirects=True))
        assert "Leche Flan" in page(juan.get("/shop/1")) and "Leche Flan" not in page(juan.get("/shop/2"))
        assert "Price must be greater than 0" in page(staff1.post(
            "/admin/menu", data={"name": "X", "category": "Meals", "price": "-1", "stock": "1"},
            follow_redirects=True))
        fields = {"name": "Chicken Adobo", "category": "Meals", "price": "60", "stock": "8"}
        staff1.post("/admin/menu/1/update", data=fields)                    # no 'available' = hide
        add_button = 'action="/shop/1/cart/add/1"'                          # only in the menu, not the sidebar
        assert add_button not in page(juan.get("/shop/1"))
        staff1.post("/admin/menu/1/update", data={**fields, "available": "on"})
        assert add_button in page(juan.get("/shop/1"))
        assert "hidden from customers" in page(staff1.post("/admin/menu/1/delete", follow_redirects=True))
        assert "Item deleted" in page(staff1.post("/admin/menu/7/delete", follow_redirects=True))

        # ---- the manager adds a shop; the shop and its login appear straight away ----
        manager = flask_app.test_client()
        response = manager.post("/admin/login", data={"account": "manager", "password": "admin123"})
        assert response.status_code == 302 and response.headers["Location"].endswith("/admin/shops")
        assert manager.get("/admin/dashboard").headers["Location"].endswith("/admin/shops")   # not a shop
        html = page(manager.get("/admin/shops"))
        assert "Mang Tomas Kitchen" in html and "Add a shop" in html
        assert "Shop added" in page(manager.post(
            "/admin/shops", data={"name": "Rice Bowl", "password": "ricebowl1"}, follow_redirects=True))
        assert "Rice Bowl" in page(manager.get("/admin/shops"))
        assert "Rice Bowl" in page(juan.get("/shops"))                       # students see it at once
        assert "Rice Bowl" in page(flask_app.test_client().get("/admin/login"))   # and so does the login page
        assert "already exists" in page(manager.post(
            "/admin/shops", data={"name": "rice bowl", "password": "another1"}, follow_redirects=True))
        assert "Password must be" in page(manager.post(
            "/admin/shops", data={"name": "Another", "password": "123"}, follow_redirects=True))
        assert "Shop name must be" in page(manager.post(
            "/admin/shops", data={"name": "R", "password": "ricebowl1"}, follow_redirects=True))
        rice = flask_app.test_client()
        assert "Wrong shop or password" in page(rice.post(
            "/admin/login", data={"account": "3", "password": shop_password}, follow_redirects=True))
        response = rice.post("/admin/login", data={"account": "3", "password": "ricebowl1"})
        assert response.headers["Location"].endswith("/admin/dashboard")
        assert "Rice Bowl" in page(rice.get("/admin/dashboard")) and "No pending orders" in page(rice.get("/admin/dashboard"))
        assert "Password changed" in page(manager.post(
            "/admin/shops/3/password", data={"password": "brandnew77"}, follow_redirects=True))
        assert "Password must be" in page(manager.post(
            "/admin/shops/3/password", data={"password": "abc"}, follow_redirects=True))
        assert "does not exist" in page(manager.post(
            "/admin/shops/999/password", data={"password": "brandnew77"}, follow_redirects=True))
        assert "Wrong shop or password" in page(flask_app.test_client().post(
            "/admin/login", data={"account": "3", "password": "ricebowl1"}, follow_redirects=True))
        assert flask_app.test_client().post(
            "/admin/login", data={"account": "3", "password": "brandnew77"}).status_code == 302

        # ---- logout (manager, shop staff and student are separate) ----
        manager.get("/admin/logout")
        assert manager.get("/admin/shops").status_code == 302
        staff1.get("/admin/logout")
        assert staff1.get("/admin/dashboard").status_code == 302
        assert juan.get("/shops").status_code == 200                       # students stay signed in
        juan.get("/logout")
        assert juan.get("/shops").status_code == 302


if __name__ == "__main__":
    test_app()
    print("All web tests passed")
