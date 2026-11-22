import uuid

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from Back_End import service

customer_bp = Blueprint("customer", __name__)


def _cart_id():
    """Each browser gets its own cart id, stored in Flask's session cookie."""
    if "cart_id" not in session:
        session["cart_id"] = uuid.uuid4().hex
    return session["cart_id"]


def _run(action, *args):
    """Call a service function. If it rejects the input, show its message."""
    try:
        action(_cart_id(), *args)
    except ValueError as error:
        flash(str(error))


def _after_cart_change():
    if request.form.get("next") == "cart":
        return redirect(url_for("customer.cart"))
    return redirect(url_for("customer.menu"))


@customer_bp.route("/menu")
def menu():
    q = request.args.get("q", "")
    sort_by = request.args.get("sort", "name")
    if sort_by not in ("name", "price"):
        sort_by = "name"
    items = service.get_menu(search=q, sort_by=sort_by)
    return render_template("costumer/menu.html", items=items, q=q, sort_by=sort_by)


@customer_bp.route("/cart")
def cart():
    lines, total = service.cart_view(_cart_id())
    return render_template("costumer/cart.html", items=lines, total=total)


@customer_bp.route("/cart/add/<int:item_id>", methods=["POST"])
def cart_add(item_id):
    _run(service.cart_add, item_id)
    return _after_cart_change()


@customer_bp.route("/cart/decrease/<int:item_id>", methods=["POST"])
def cart_decrease(item_id):
    _run(service.cart_decrease, item_id)
    return redirect(url_for("customer.cart"))


@customer_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
def cart_remove(item_id):
    _run(service.cart_remove, item_id)
    return redirect(url_for("customer.cart"))


@customer_bp.route("/cart/undo", methods=["POST"])
def cart_undo():
    _run(service.cart_undo)
    return redirect(url_for("customer.cart"))


@customer_bp.route("/checkout", methods=["POST"])
def checkout():
    table_no = request.form.get("table_no", "")
    urgent = "urgent" in request.form
    try:
        order_no = service.place_order(_cart_id(), table_no, urgent)
    except ValueError as error:
        flash(str(error))
        return redirect(url_for("customer.cart"))
    return redirect(url_for("customer.order_status", order_no=order_no))


@customer_bp.route("/order/<int:order_no>")
def order_status(order_no):
    order = service.find_order(order_no)
    if order is None:
        return "Order not found", 404
    return render_template("costumer/status.html", order=order)


@customer_bp.route("/order/<int:order_no>/live")
def order_status_live(order_no):
    order = service.find_order(order_no)
    if order is None:
        return "Order not found", 404
    return render_template("costumer/_order_card.html", order=order)
