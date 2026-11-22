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
    return session["student"]


def _shop_or_404(shop_id):
    try:
        return service.get_shop(shop_id)
    except ValueError:
        return None


def _is_ajax():
    """The page's JavaScript sends this header so we reply with just the cart box."""
    return request.headers.get("X-Requested-With") == "fetch"


def _cart_box(shop, show_flashes):
    lines, total = service.cart_view(_email(), shop["id"])
    return render_template("costumer/_cart_box.html", shop=shop, cart_items=lines,
                           cart_total=total, show_flashes=show_flashes)


def _after_cart_change(shop):
    if _is_ajax():
        return _cart_box(shop, show_flashes=True)      # the messages travel inside the box
    return redirect(url_for("customer.shop", shop_id=shop["id"]))


def _cart_action(shop_id, action, *args):
    shop = _shop_or_404(shop_id)
    if shop is None:
        return "Shop not found", 404
    try:
        action(_email(), shop_id, *args)
    except ValueError as error:
        flash(str(error))
    return _after_cart_change(shop)


def _my_order(order_no):
    """The order, but only if it belongs to the signed-in student."""
    order = service.find_order(order_no)
    if order is None or order["customer_email"] != _email():
        return None
    return order


@customer_bp.route("/menu")
@student_required
def menu():
    return redirect(url_for("customer.shops"))


@customer_bp.route("/shops")
@student_required
def shops():
    return render_template("costumer/shops.html", shops=service.shop_cards())


@customer_bp.route("/shop/<int:shop_id>")
@student_required
def shop(shop_id):
    the_shop = _shop_or_404(shop_id)
    if the_shop is None:
        return "Shop not found", 404
    q = request.args.get("q", "")
    sort_by = request.args.get("sort", "name")
    if sort_by not in ("name", "price"):
        sort_by = "name"
    items = service.get_menu(shop_id, search=q, sort_by=sort_by)
    lines, total = service.cart_view(_email(), shop_id)
    return render_template("costumer/shop.html", shop=the_shop, items=items, q=q, sort_by=sort_by,
                           cart_items=lines, cart_total=total, show_flashes=False,
                           my_orders=service.my_orders(_email(), limit=8))


@customer_bp.route("/shop/<int:shop_id>/orders-box")
@student_required
def orders_box(shop_id):
    if _shop_or_404(shop_id) is None:
        return "Shop not found", 404
    return render_template("costumer/_orders_box.html",
                           my_orders=service.my_orders(_email(), limit=8))


@customer_bp.route("/shop/<int:shop_id>/cart/add/<int:item_id>", methods=["POST"])
@student_required
def cart_add(shop_id, item_id):
    return _cart_action(shop_id, service.cart_add, item_id)


@customer_bp.route("/shop/<int:shop_id>/cart/decrease/<int:item_id>", methods=["POST"])
@student_required
def cart_decrease(shop_id, item_id):
    return _cart_action(shop_id, service.cart_decrease, item_id)


@customer_bp.route("/shop/<int:shop_id>/cart/remove/<int:item_id>", methods=["POST"])
@student_required
def cart_remove(shop_id, item_id):
    return _cart_action(shop_id, service.cart_remove, item_id)


@customer_bp.route("/shop/<int:shop_id>/cart/undo", methods=["POST"])
@student_required
def cart_undo(shop_id):
    return _cart_action(shop_id, service.cart_undo)


@customer_bp.route("/shop/<int:shop_id>/checkout", methods=["POST"])
@student_required
def checkout(shop_id):
    shop = _shop_or_404(shop_id)
    if shop is None:
        return "Shop not found", 404
    table_no = request.form.get("table_no", "")
    urgent = "urgent" in request.form
    try:
        order_no = service.place_order(_email(), shop_id, table_no, urgent)
        flash(f"Order #{order_no} placed!")
    except ValueError as error:
        flash(str(error))
    return _after_cart_change(shop)


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
