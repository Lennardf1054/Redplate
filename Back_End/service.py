import math
import re
import sqlite3
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

import config
from Back_End import database as db
from Back_End.algorithm import binary_search, merge_sort
from Back_End.Structures.bst import BST
from Back_End.Structures.hash_table import HashTable
from Back_End.Structures.heap import MinHeap
from Back_End.Structures.queue import Queue
from Back_End.Structures.stack import Stack

STATUSES = ["Pending", "Preparing", "Ready", "Completed"]
MAX_TABLE_NO = 50
MAX_QTY_PER_ITEM = 10
URGENT_MINUTES = 10

# The in-memory structures. init() fills them from the database.
_menu = None            # Hash Table: item id -> item dict
_orders = None          # BST: order number -> order dict (the record store)
_order_list = None      # list of the same order dicts, sorted by order number (for binary search)
_normal_queue = None    # Queue: order numbers of normal pending orders
_urgent_heap = None     # Min-Heap: (priority, order number) of urgent pending orders
_carts = None           # Hash Table: session id -> Cart
_next_order_no = 1


# ---------- STARTUP ----------

def init():
    """Create the database if needed, then load everything into the structures."""
    global _menu, _orders, _order_list, _normal_queue, _urgent_heap, _carts, _next_order_no
    db.create_tables()
    db.seed_sample_data()
    ensure_admin()

    _menu = HashTable()
    for item in db.load_menu_items():
        item["price"] = _tidy(item["price"])
        _menu.put(item["id"], item)

    _orders = BST()
    _normal_queue = Queue()
    _urgent_heap = MinHeap()
    _carts = HashTable()

    for order in db.load_orders():                     # oldest first
        order["total"] = _tidy(order["total"])
        for line in order["items"]:
            line["price"] = _tidy(line["price"])
            line["name"] = _menu.get(line["menu_item_id"])["name"]
        _orders.insert(order["order_no"], order)
        if order["status"] == "Pending":
            _enqueue_pending(order)

    _order_list = [order for _, order in _orders.inorder()]   # the BST hands them over sorted
    _next_order_no = db.get_max_order_no() + 1


def ensure_admin():
    """Create the default admin account if none exists. Only the hash is stored."""
    if db.get_admin(config.ADMIN_USERNAME) is None:
        db.add_admin(
            config.ADMIN_USERNAME,
            generate_password_hash(config.ADMIN_PASSWORD, method="pbkdf2:sha256"),
        )


def check_admin(username, password):
    admin = db.get_admin(username)
    return admin is not None and check_password_hash(admin["password_hash"], password)


_EMAIL_NAME = re.compile(r"^[a-z0-9._%+-]{1,64}$")


def check_student_email(email):
    """Accept only school Google accounts. Returns the cleaned-up email."""
    email = str(email).strip().lower()
    domain = config.ALLOWED_EMAIL_DOMAIN.lower()
    name, _, host = email.rpartition("@")
    if not name or host != domain or not _EMAIL_NAME.match(name):
        raise ValueError(f"Please use your school Google account (@{domain})")
    return email


def _tidy(number):
    """60.0 -> 60, so prices don't show as 60.0 on the pages."""
    number = float(number)
    return int(number) if number.is_integer() else round(number, 2)


# ---------- SCHEDULING (Queue + Min-Heap) ----------

def _enqueue_pending(order):
    if order["priority"] == 0:
        _urgent_heap.push((0, order["order_no"]))      # urgent lane
    else:
        _normal_queue.enqueue(order["order_no"])       # normal lane


def _is_pending(order_no):
    index = binary_search(_order_list, order_no)
    return index != -1 and _order_list[index]["status"] == "Pending"


def _next_to_serve():
    """Order number to serve next, or None. Urgent lane first, then the queue.
    Orders that are no longer Pending are thrown away when they reach the front
    (lazy deletion), so we never have to remove from the middle of a queue."""
    while not _urgent_heap.is_empty():
        order_no = _urgent_heap.peek()[1]
        if _is_pending(order_no):
            return order_no
        _urgent_heap.pop()
    while not _normal_queue.is_empty():
        order_no = _normal_queue.peek()
        if _is_pending(order_no):
            return order_no
        _normal_queue.dequeue()
    return None


# ---------- MENU (Hash Table) ----------

def _get_item(item_id):
    if not _menu.contains(item_id):
        raise ValueError("That menu item does not exist")
    return _menu.get(item_id)


def get_menu(search="", sort_by="name", include_hidden=False):
    search = search.strip().lower()
    if sort_by not in ("name", "price"):
        sort_by = "name"
    items = []
    for _, item in _menu.items():
        if not include_hidden and not item["is_available"]:
            continue
        if search and search not in item["name"].lower():
            continue
        items.append(item)
    return merge_sort(items, sort_by)


def _clean_menu_input(name, category, price, stock):
    name = str(name).strip()
    category = str(category).strip() or "Meals"
    if not name or len(name) > 50:
        raise ValueError("Name is required (50 characters max)")
    try:
        price = float(price)
    except (TypeError, ValueError):
        raise ValueError("Price must be a number")
    if not math.isfinite(price) or price <= 0:
        raise ValueError("Price must be greater than 0")
    try:
        stock = int(stock)
    except (TypeError, ValueError):
        raise ValueError("Stock must be a whole number")
    if stock < 0:
        raise ValueError("Stock cannot be negative")
    return name, category, _tidy(price), stock


def add_menu_item(name, category, price, stock):
    name, category, price, stock = _clean_menu_input(name, category, price, stock)
    item_id = db.add_menu_item(name, category, price, stock)      # save first
    _menu.put(item_id, {"id": item_id, "name": name, "category": category,
                        "price": price, "stock": stock, "is_available": 1})
    return item_id


def update_menu_item(item_id, name, category, price, stock, available=None):
    """available=None keeps the current setting; True or False shows or hides the item."""
    item = _get_item(item_id)
    name, category, price, stock = _clean_menu_input(name, category, price, stock)
    is_available = item["is_available"] if available is None else (1 if available else 0)
    db.update_menu_item(item_id, name, category, price, stock, is_available)
    item.update(name=name, category=category, price=price, stock=stock,
                is_available=is_available)


def remove_menu_item(item_id):
    """Delete the item. If past orders use it, hide it instead. Returns what happened."""
    item = _get_item(item_id)
    try:
        db.delete_menu_item(item_id)
    except sqlite3.IntegrityError:                     # old orders still point to it
        db.update_menu_item(item_id, item["name"], item["category"],
                            item["price"], item["stock"], 0)
        item["is_available"] = 0
        return "hidden"
    _menu.remove(item_id)
    return "deleted"


# ---------- CART (Hash Table + Stack) ----------

class Cart:
    """One customer's cart. Hash Table = item id -> quantity. Stack = undo history."""

    def __init__(self):
        self.lines = HashTable()
        self.history = Stack()

    def is_empty(self):
        return self.lines.size() == 0

    def qty(self, item_id):
        return self.lines.get(item_id) if self.lines.contains(item_id) else 0

    def set_qty(self, item_id, new_qty):
        self.history.push((item_id, self.qty(item_id)))   # remember the OLD quantity
        self._apply(item_id, new_qty)

    def undo(self):
        if self.history.is_empty():
            raise IndexError("Nothing to undo")
        item_id, old_qty = self.history.pop()
        self._apply(item_id, old_qty)

    def _apply(self, item_id, qty):
        if qty > 0:
            self.lines.put(item_id, qty)
        elif self.lines.contains(item_id):
            self.lines.remove(item_id)


def _get_cart(session_id):
    if not _carts.contains(session_id):
        _carts.put(session_id, Cart())
    return _carts.get(session_id)


def cart_add(session_id, item_id):
    item = _get_item(item_id)
    cart = _get_cart(session_id)
    new_qty = cart.qty(item_id) + 1
    if not item["is_available"] or item["stock"] <= 0:
        raise ValueError(f'{item["name"]} is out of stock')
    if new_qty > item["stock"]:
        raise ValueError(f'Only {item["stock"]} {item["name"]} left')
    if new_qty > MAX_QTY_PER_ITEM:
        raise ValueError(f"You can order at most {MAX_QTY_PER_ITEM} of one item")
    cart.set_qty(item_id, new_qty)


def cart_decrease(session_id, item_id):
    cart = _get_cart(session_id)
    qty = cart.qty(item_id)
    if qty == 0:
        raise ValueError("That item is not in your cart")
    cart.set_qty(item_id, qty - 1)


def cart_remove(session_id, item_id):
    cart = _get_cart(session_id)
    if cart.qty(item_id) == 0:
        raise ValueError("That item is not in your cart")
    cart.set_qty(item_id, 0)


def cart_undo(session_id):
    try:
        _get_cart(session_id).undo()
    except IndexError:
        raise ValueError("Nothing to undo")


def cart_view(session_id):
    """Returns (lines, total). Each line: id, name, price, qty."""
    cart = _get_cart(session_id)
    lines = []
    total = 0
    for item_id, qty in cart.lines.items():
        if not _menu.contains(item_id):                # the admin deleted it meanwhile
            cart._apply(item_id, 0)
            continue
        item = _menu.get(item_id)
        lines.append({"id": item_id, "name": item["name"], "price": item["price"], "qty": qty})
        total += item["price"] * qty
    return merge_sort(lines, "id"), total


# ---------- ORDERS (Queue + Min-Heap + BST + binary search) ----------

def _check_table_no(table_no):
    table_no = str(table_no).strip()
    if not table_no.isdecimal() or not 1 <= int(table_no) <= MAX_TABLE_NO:
        raise ValueError(f"Table number must be from 1 to {MAX_TABLE_NO}")
    return str(int(table_no))


def place_order(session_id, table_no, urgent=False, customer_email=""):
    """Turn the cart into an order. Returns the new order number."""
    global _next_order_no
    table_no = _check_table_no(table_no)
    if not _carts.contains(session_id) or _carts.get(session_id).is_empty():
        raise ValueError("Your cart is empty")
    cart = _carts.get(session_id)

    lines = []                                         # re-check stock at the last moment
    total = 0
    for item_id, qty in cart.lines.items():
        item = _get_item(item_id)
        if not item["is_available"] or qty > item["stock"]:
            raise ValueError(f'Not enough stock for {item["name"]}')
        lines.append({"menu_item_id": item_id, "name": item["name"],
                      "quantity": qty, "price": item["price"]})
        total += item["price"] * qty

    order_no = _next_order_no
    priority = 0 if urgent else 1
    created_at = db.save_order(order_no, table_no, "Pending", priority, total, lines,
                               customer_email)

    order = {"order_no": order_no, "table_no": table_no, "status": "Pending",
             "priority": priority, "total": total, "created_at": created_at,
             "items": lines, "customer_email": customer_email}
    _orders.insert(order_no, order)                    # BST: store the record
    _order_list.append(order)                          # still sorted: new numbers are the biggest
    _enqueue_pending(order)                            # Queue or Min-Heap: schedule it

    for line in lines:                                 # take the stock
        item = _menu.get(line["menu_item_id"])
        item["stock"] -= line["quantity"]
        db.update_stock(item["id"], item["stock"])

    _next_order_no += 1
    _carts.remove(session_id)
    return order_no


def update_status(order_no, new_status):
    order = _find_record(order_no)
    if new_status not in STATUSES:
        raise ValueError("Unknown status")
    if STATUSES.index(new_status) != STATUSES.index(order["status"]) + 1:
        raise ValueError(f'Cannot change {order["status"]} to {new_status}')
    db.update_order_status(order_no, new_status)       # save first
    order["status"] = new_status


def _find_record(order_no):
    index = binary_search(_order_list, order_no)       # our own binary search
    if index == -1:
        raise ValueError(f"Order #{order_no} not found")
    return _order_list[index]


def _order_view(order):
    """The simple dict the HTML templates use."""
    created = datetime.fromisoformat(order["created_at"])
    waiting = int((datetime.now() - created).total_seconds() // 60)
    parts = [f'{line["quantity"]}x {line["name"]}' for line in order["items"]]
    return {
        "order_no": order["order_no"],
        "table_no": order["table_no"],
        "items_text": ", ".join(parts),
        "status": order["status"],
        "total": order["total"],
        "minutes_waiting": waiting,
        "urgent": order["priority"] == 0 or waiting >= URGENT_MINUTES,
        "customer_email": order.get("customer_email", ""),
    }


def find_order(order_no):
    index = binary_search(_order_list, order_no)
    return _order_view(_order_list[index]) if index != -1 else None


def my_orders(customer_email):
    """One student's orders, newest first."""
    mine = [order for order in _order_list if order["customer_email"] == customer_email]
    return [_order_view(order) for order in reversed(mine)]


def all_orders():
    return [_order_view(order) for _, order in _orders.inorder()]


def dashboard():
    """Returns (next order to serve or None, list of active orders)."""
    next_no = _next_to_serve()
    next_view = find_order(next_no) if next_no is not None else None
    active = [_order_view(order) for _, order in _orders.inorder()
              if order["status"] in ("Pending", "Preparing", "Ready")]
    return next_view, active


def sales_report(sort_by="order_no"):
    """Returns (completed orders, total sales, sort used)."""
    if sort_by not in ("order_no", "total"):
        sort_by = "order_no"
    completed = [_order_view(order) for _, order in _orders.inorder()
                 if order["status"] == "Completed"]
    completed = merge_sort(completed, sort_by)
    total_sales = sum(order["total"] for order in completed)
    return completed, total_sales, sort_by
