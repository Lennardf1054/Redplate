from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from Back_End import service

customer_bp = Blueprint("customer", __name__)


def student_required(view):
    """Put this under @route to send anyone who is not signed in to the login page."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("student"):
            flash("Please sign in with your school Google account first")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapper


def _email():
    return session["student"]                          # also the key of this student's cart


def _run(action, *args):
    """Call a service function. If it rejects the input, show its message."""
    try:
        action(_email(), *args)
    except ValueError as error:
        flash(str(error))


def _after_cart_change():
    if request.form.get("next") == "cart":
        return redirect(url_for("customer.cart"))
    return redirect(url_for("customer.menu"))


def _my_order(order_no):
    """The order, but only if it belongs to the signed-in student."""
    order = service.find_order(order_no)
    if order is None or order["customer_email"] != _email():
        return None
    return order


@customer_bp.route("/menu")
@student_required
def menu():
    q = request.args.get("q", "")
    sort_by = request.args.get("sort", "name")
    if sort_by not in ("name", "price"):
        sort_by = "name"
    items = service.get_menu(search=q, sort_by=sort_by)
    return render_template("costumer/menu.html", items=items, q=q, sort_by=sort_by)


@customer_bp.route("/cart")
@student_required
def cart():
    lines, total = service.cart_view(_email())
    return render_template("costumer/cart.html", items=lines, total=total)


@customer_bp.route("/cart/add/<int:item_id>", methods=["POST"])
@student_required
def cart_add(item_id):
    _run(service.cart_add, item_id)
    return _after_cart_change()


@customer_bp.route("/cart/decrease/<int:item_id>", methods=["POST"])
@student_required
def cart_decrease(item_id):
    _run(service.cart_decrease, item_id)
    return redirect(url_for("customer.cart"))


@customer_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
@student_required
def cart_remove(item_id):
    _run(service.cart_remove, item_id)
    return redirect(url_for("customer.cart"))


@customer_bp.route("/cart/undo", methods=["POST"])
@student_required
def cart_undo():
    _run(service.cart_undo)
    return redirect(url_for("customer.cart"))


@customer_bp.route("/checkout", methods=["POST"])
@student_required
def checkout():
    table_no = request.form.get("table_no", "")
    urgent = "urgent" in request.form
    try:
        order_no = service.place_order(_email(), table_no, urgent, customer_email=_email())
    except ValueError as error:
        flash(str(error))
        return redirect(url_for("customer.cart"))
    return redirect(url_for("customer.order_status", order_no=order_no))


@customer_bp.route("/my-orders")
@student_required
def my_orders():
    return render_template("costumer/my_orders.html", orders=service.my_orders(_email()))


@customer_bp.route("/order/<int:order_no>")
@student_required
def order_status(order_no):
    order = _my_order(order_no)
    if order is None:
        return "Order not found", 404
    return render_template("costumer/status.html", order=order)


@customer_bp.route("/order/<int:order_no>/live")
@student_required
def order_status_live(order_no):
    order = _my_order(order_no)
    if order is None:
        return "Order not found", 404
    return render_template("costumer/_order_card.html", order=order)
