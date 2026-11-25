from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

import config
from Back_End import service

admin_bp = Blueprint("admin", __name__)


def shop_required(view):
    """Only a signed-in shop may open the page, and only for its own shop."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if session.get("shop_id") is None:
            if session.get("manager"):
                flash("Sign in as a shop to use that page")
                return redirect(url_for("admin.shops"))
            flash("Please log in first")
            return redirect(url_for("admin.login"))
        try:
            shop = service.get_shop(session["shop_id"])
        except ValueError:                             # the manager deleted this shop
            for key in ("shop_id", "shop_name"):
                session.pop(key, None)
            flash("That shop no longer exists")
            return redirect(url_for("admin.login"))
        session["shop_name"] = shop["name"]            # picks up a rename right away
        return view(session["shop_id"], *args, **kwargs)
    return wrapper


def manager_required(view):
    """Only the canteen manager may open the page."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("manager"):
            flash("Please log in as the canteen manager first")
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)
    return wrapper


# ---------- login: each shop has its own password, the manager has another ----------

@admin_bp.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        account = request.form.get("account", "")
        password = request.form.get("password", "")
        if account == "manager":
            if service.check_admin(config.ADMIN_USERNAME, password):
                session.pop("shop_id", None)
                session.pop("shop_name", None)
                session["manager"] = True
                return redirect(url_for("admin.shops"))
        else:
            try:
                shop_id = int(account)
            except ValueError:
                shop_id = None
            if shop_id is not None and service.check_shop_login(shop_id, password):
                session.pop("manager", None)
                session["shop_id"] = shop_id
                session["shop_name"] = service.get_shop(shop_id)["name"]
                return redirect(url_for("admin.dashboard"))
        flash("Wrong shop or password")
    return render_template("admin/login.html", shops=service.list_shops())


@admin_bp.route("/admin/logout")
def logout():
    for key in ("manager", "shop_id", "shop_name"):
        session.pop(key, None)
    return redirect(url_for("admin.login"))


# ---------- the canteen manager: add shops ----------

@admin_bp.route("/admin/shops", methods=["GET", "POST"])
@manager_required
def shops():
    if request.method == "POST":
        try:
            service.add_shop(request.form.get("name", ""), request.form.get("password", ""))
            flash("Shop added. Its login account is ready.")
        except ValueError as error:
            flash(str(error))
        return redirect(url_for("admin.shops"))
    return render_template("admin/shops.html", shops=service.list_shops())

@admin_bp.route("/admin/shops/<int:shop_id>/rename", methods=["POST"])
@manager_required
def rename_shop(shop_id):
    try:
        service.rename_shop(shop_id, request.form.get("name", ""))
        flash("Shop renamed")
    except ValueError as error:
        flash(str(error))
    return redirect(url_for("admin.shops"))


@admin_bp.route("/admin/shops/<int:shop_id>/password", methods=["POST"])
@manager_required
def reset_shop_password(shop_id):
    try:
        service.reset_shop_password(shop_id, request.form.get("password", ""))
        flash("Password changed")
    except ValueError as error:
        flash(str(error))
    return redirect(url_for("admin.shops"))

@admin_bp.route("/admin/shops/<int:shop_id>/delete", methods=["POST"])
@manager_required
def delete_shop(shop_id):
    try:
        service.delete_shop(shop_id)
        flash("Shop deleted")
    except ValueError as error:
        flash(str(error))
    return redirect(url_for("admin.shops"))

# ---------- one shop's staff: everything below only touches their own shop ----------

@admin_bp.route("/admin/dashboard")
@shop_required
def dashboard(shop_id):
    next_order, orders = service.dashboard(shop_id)
    return render_template("admin/dashboard.html", orders=orders, next_order=next_order)


@admin_bp.route("/admin/dashboard/live")
@shop_required
def dashboard_live(shop_id):
    next_order, orders = service.dashboard(shop_id)
    return render_template("admin/_dashboard_live.html", orders=orders, next_order=next_order)


@admin_bp.route("/admin/orders/<int:order_no>/status", methods=["POST"])
@shop_required
def update_status(shop_id, order_no):
    try:
        service.update_status(shop_id, order_no, request.form.get("status", ""))
    except ValueError as error:
        flash(str(error))
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/admin/orders")
@shop_required
def orders(shop_id):
    search = request.args.get("order_id", "").strip()
    message = ""
    if not search:
        orders_to_show = service.all_orders(shop_id)
    elif not search.isdecimal() or len(search) > 9:
        orders_to_show = []
        message = "Please enter a valid order number."
    else:
        order = service.find_shop_order(shop_id, int(search))
        orders_to_show = [order] if order else []
        if not order:
            message = "No order found with that number."
    return render_template("admin/orders.html", orders=orders_to_show, message=message)


@admin_bp.route("/admin/menu", methods=["GET", "POST"])
@shop_required
def menu(shop_id):
    if request.method == "POST":
        try:
            service.add_menu_item(
                shop_id,
                request.form.get("name", ""),
                request.form.get("category", ""),
                request.form.get("price", ""),
                request.form.get("stock", ""),
            )
            flash("Item added")
        except ValueError as error:
            flash(str(error))
        return redirect(url_for("admin.menu"))
    items = service.get_menu(shop_id, include_hidden=True)
    return render_template("admin/menu_manage.html", items=items)


@admin_bp.route("/admin/menu/<int:item_id>/update", methods=["POST"])
@shop_required
def update_item(shop_id, item_id):
    try:
        service.update_menu_item(
            shop_id,
            item_id,
            request.form.get("name", ""),
            request.form.get("category", ""),
            request.form.get("price", ""),
            request.form.get("stock", ""),
            available="available" in request.form,
        )
        flash("Item updated")
    except ValueError as error:
        flash(str(error))
    return redirect(url_for("admin.menu"))


@admin_bp.route("/admin/menu/<int:item_id>/delete", methods=["POST"])
@shop_required
def delete_item(shop_id, item_id):
    try:
        result = service.remove_menu_item(shop_id, item_id)
        if result == "deleted":
            flash("Item deleted")
        else:
            flash("This item is in past orders, so it was hidden from customers instead. "
                  "Tick Shown and press Save to bring it back.")
    except ValueError as error:
        flash(str(error))
    return redirect(url_for("admin.menu"))


@admin_bp.route("/admin/reports")
@shop_required
def reports(shop_id):
    completed, total_sales, sort_by = service.sales_report(shop_id, request.args.get("sort", "order_no"))
    return render_template("admin/reports.html", orders=completed,
                           total_sales=total_sales, sort_by=sort_by)
