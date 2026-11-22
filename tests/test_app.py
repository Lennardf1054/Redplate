"""Web-level test: drives the whole site with Flask's test client (no browser, no internet).
Run from the Redplate folder:  python -m tests.test_app
"""
import os
import tempfile

import config
from Back_End import database as db


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

    with tempfile.TemporaryDirectory() as folder:
        db.use_database(os.path.join(folder, "test.db"))     # never touch the real database
        import app as app_module                             # app.py loads the data on import
        from Back_End.routes import auth
        juan = app_module.app.test_client()

        # ---- not signed in: everything customer-side sends you to the login page ----
        for method, url in (("get", "/"), ("get", "/menu"), ("get", "/cart"), ("get", "/my-orders"),
                            ("get", "/order/1"), ("post", "/cart/add/1"), ("post", "/checkout")):
            response = getattr(juan, method)(url)
            assert response.status_code == 302 and response.headers["Location"].endswith("/login"), url
        html = page(juan.get("/login"))
        assert "Sign in with Google" in html and "Demo mode" in html

        # ---- demo sign-in: only school accounts ----
        assert "Please use your school Google account" in page(
            juan.post("/auth/demo", data={"email": "juan@gmail.com"}, follow_redirects=True))
        response = juan.post("/auth/demo", data={"email": "juan@" + domain})
        assert response.status_code == 302 and response.headers["Location"].endswith("/menu")
        assert juan.get("/login").status_code == 302                         # already signed in

        # ---- customer side ----
        html = page(juan.get("/menu"))
        assert "Chicken Adobo" in html and "Pancit Canton" in html and "My Orders" in html
        html = page(juan.get("/menu?q=adobo"))
        assert "Chicken Adobo" in html and "Pancit Canton" not in html
        assert juan.get("/menu?sort=hacker").status_code == 200              # bad sort is ignored

        juan.post("/cart/add/1")
        html = page(juan.get("/cart"))
        assert "Chicken Adobo" in html and "Total" in html
        assert "out of stock" in page(juan.post("/cart/add/3", follow_redirects=True))
        juan.post("/cart/undo")
        assert "Your cart is empty" in page(juan.get("/cart"))
        assert "Nothing to undo" in page(juan.post("/cart/undo", follow_redirects=True))

        juan.post("/cart/add/1")
        assert "Table number must be" in page(
            juan.post("/checkout", data={"table_no": "0"}, follow_redirects=True))
        assert "Table number must be" in page(
            juan.post("/checkout", data={"table_no": "abc"}, follow_redirects=True))
        response = juan.post("/checkout", data={"table_no": "5", "urgent": "on"})
        assert response.status_code == 302 and response.headers["Location"].endswith("/order/1")
        html = page(juan.get("/order/1"))
        assert "Order #1" in html and 'step active">Pending' in html
        assert "#1" in page(juan.get("/my-orders"))
        assert juan.get("/order/999").status_code == 404
        assert juan.get("/nope").status_code == 404

        # ---- another student cannot see Juan's order ----
        maria = app_module.app.test_client()
        maria.post("/auth/demo", data={"email": "maria@" + domain})
        assert maria.get("/order/1").status_code == 404
        assert maria.get("/order/1/live").status_code == 404
        assert "no orders yet" in page(maria.get("/my-orders"))
        maria.post("/cart/add/1")
        assert "Your cart is empty" not in page(maria.get("/cart"))         # her own cart
        assert "Your cart is empty" in page(juan.get("/cart"))              # and Juan's is separate

        # ---- sign in with Google (Google's servers are replaced by fakes) ----
        pedro = app_module.app.test_client()
        response = pedro.get("/auth/google")
        location = response.headers["Location"]
        assert response.status_code == 302 and location.startswith("https://accounts.google.com/")
        assert "client_id=test-client" in location and "scope=openid+email" in location
        with pedro.session_transaction() as session:
            state = session["oauth_state"]
        auth._post_form = lambda url, data: {"access_token": "token"}
        auth._get_json = lambda url, token: {"email": "pedro@" + domain, "email_verified": True}
        response = pedro.get("/auth/google/callback?code=abc&state=" + state)
        assert response.status_code == 302 and response.headers["Location"].endswith("/menu")
        assert pedro.get("/menu").status_code == 200

        def google_attempt(post_form, get_json, give_state=True, extra=""):
            client = app_module.app.test_client()
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
        assert "Could not sign in" in google_attempt(lambda u, d: {}, lambda u, t: {})   # no token in reply

        config.DEMO_LOGIN = False                                           # demo sign-in can be turned off
        assert "turned off" in page(app_module.app.test_client().post(
            "/auth/demo", data={"email": "x@" + domain}, follow_redirects=True))
        config.DEMO_LOGIN = True

        # ---- admin side is protected ----
        admin = app_module.app.test_client()
        for url in ("/admin/dashboard", "/admin/orders", "/admin/menu", "/admin/reports",
                    "/admin/dashboard/live"):
            response = admin.get(url)
            assert response.status_code == 302 and "/admin/login" in response.headers["Location"]
        assert juan.get("/admin/dashboard").status_code == 302              # a student is not an admin
        assert admin.post("/admin/orders/1/status", data={"status": "Preparing"}).status_code == 302
        assert "Wrong username or password" in page(
            admin.post("/admin/login", data={"username": "admin", "password": "nope"},
                       follow_redirects=True))
        response = admin.post("/admin/login", data={"username": "admin", "password": "admin123"})
        assert response.status_code == 302 and response.headers["Location"].endswith("/admin/dashboard")

        # ---- admin: dashboard and status ----
        html = page(admin.get("/admin/dashboard"))
        assert "Next to serve" in html and "#1" in html and "URGENT" in html
        assert "1x Chicken Adobo" in html
        assert "Mark Preparing" in page(admin.get("/admin/dashboard/live"))
        assert "Cannot change" in page(admin.post(
            "/admin/orders/1/status", data={"status": "Completed"}, follow_redirects=True))
        admin.post("/admin/orders/1/status", data={"status": "Preparing"})
        assert 'step active">Preparing' in page(juan.get("/order/1/live"))  # the student sees it
        admin.post("/admin/orders/1/status", data={"status": "Ready"})
        admin.post("/admin/orders/1/status", data={"status": "Completed"})

        # ---- admin: all orders and search ----
        html = page(admin.get("/admin/orders"))
        assert "1x Chicken Adobo" in html and "built-in method" not in html
        assert "1x Chicken Adobo" in page(admin.get("/admin/orders?order_id=1"))
        assert "No order found" in page(admin.get("/admin/orders?order_id=999"))
        assert "valid order number" in page(admin.get("/admin/orders?order_id=abc"))
        assert "valid order number" in page(admin.get("/admin/orders?order_id=99999999999"))

        # ---- admin: report ----
        html = page(admin.get("/admin/reports?sort=total"))
        assert "Total sales" in html and "₱60" in html and "built-in method" not in html
        assert admin.get("/admin/reports?sort=hacker").status_code == 200

        # ---- admin: menu management ----
        assert "Chicken Adobo" in page(admin.get("/admin/menu"))
        assert "Item added" in page(admin.post(
            "/admin/menu", data={"name": "Halo-Halo", "category": "Snacks", "price": "45", "stock": "8"},
            follow_redirects=True))
        assert "Price must be greater than 0" in page(admin.post(
            "/admin/menu", data={"name": "X", "category": "Meals", "price": "-1", "stock": "1"},
            follow_redirects=True))
        fields = {"name": "Chicken Adobo", "category": "Meals", "price": "60", "stock": "8"}
        admin.post("/admin/menu/1/update", data=fields)                     # no 'available' = hide
        assert "Chicken Adobo" not in page(juan.get("/menu"))
        admin.post("/admin/menu/1/update", data={**fields, "available": "on"})
        assert "Chicken Adobo" in page(juan.get("/menu"))
        assert "hidden from customers" in page(admin.post("/admin/menu/1/delete",
                                                          follow_redirects=True))
        assert "Item deleted" in page(admin.post("/admin/menu/5/delete", follow_redirects=True))

        # ---- logout (admin and student are separate) ----
        admin.get("/admin/logout")
        assert admin.get("/admin/dashboard").status_code == 302
        juan.get("/logout")
        assert juan.get("/menu").status_code == 302


if __name__ == "__main__":
    test_app()
    print("All web tests passed")
