from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from Back_End import service

admin_bp = Blueprint("admin", __name__)


def admin_required(view):
    """Put this under @route to block anyone who is not logged in as admin."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            flash("Please log in as admin first")
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)
    return wrapper


@admin_bp.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if service.check_admin(username, password):
            session["admin"] = username
            return redirect(url_for("admin.dashboard"))
        flash("Wrong username or password")
    return render_template("admin/login.html")


@admin_bp.route("/admin/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin.login"))


@admin_bp.route("/admin/dashboard")
@admin_required
def dashboard():
    next_order, orders = service.dashboard()
    return render_template("admin/dashboard.html", orders=orders, next_order=next_order)


@admin_bp.route("/admin/dashboard/live")
@admin_required
def dashboard_live():
    next_order, orders = service.dashboard()
    return render_template("admin/_dashboard_live.html", orders=orders, next_order=next_order)


@admin_bp.route("/admin/orders/<int:order_no>/status", methods=["POST"])
@admin_required
def update_status(order_no):
    try:
        service.update_status(order_no, request.form.get("status", ""))
    except ValueError as error:
        flash(str(error))
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/admin/orders")
@admin_required
def orders():
    search = request.args.get("order_id", "").strip()
    message = ""
    if not search:
        orders_to_show = service.all_orders()
    elif not search.isdecimal() or len(search) > 9:
        orders_to_show = []
        message = "Please enter a valid order number."
    else:
        order = service.find_order(int(search))
        orders_to_show = [order] if order else []
        if not order:
            message = "No order found with that number."
    return render_template("admin/orders.html", orders=orders_to_show, message=message)


@admin_bp.route("/admin/menu", methods=["GET", "POST"])
@admin_required
def menu():
    if request.method == "POST":
        try:
            service.add_menu_item(
                request.form.get("name", ""),
                request.form.get("category", ""),
                request.form.get("price", ""),
                request.form.get("stock", ""),
            )
            flash("Item added")
        except ValueError as error:
            flash(str(error))
        return redirect(url_for("admin.menu"))
    items = service.get_menu(include_hidden=True)
    return render_template("admin/menu_manage.html", items=items)


@admin_bp.route("/admin/menu/<int:item_id>/update", methods=["POST"])
@admin_required
def update_item(item_id):
    try:
        service.update_menu_item(
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
@admin_required
def delete_item(item_id):
    try:
        result = service.remove_menu_item(item_id)
        if result == "deleted":
            flash("Item deleted")
        else:
            flash("This item is in past orders, so it was hidden from customers instead. "
                  "Tick Shown and press Save to bring it back.")
    except ValueError as error:
        flash(str(error))
    return redirect(url_for("admin.menu"))


@admin_bp.route("/admin/reports")
@admin_required
def reports():
    completed, total_sales, sort_by = service.sales_report(request.args.get("sort", "order_no"))
    return render_template("admin/reports.html", orders=completed,
                           total_sales=total_sales, sort_by=sort_by)
