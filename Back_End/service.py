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
MIN_PASSWORD_LENGTH = 6

# Shops created the very first time the app runs on an empty database.
SAMPLE_SHOPS = [
    ("Julies", [("Chicken Adobo", "Meals", 60, 10),
                            ("Pancit Canton", "Meals", 35, 5),
                            ("Plain Rice", "Meals", 10, 30)]),
    ("Potato Corner", [("Iced Tea", "Drinks", 20, 0),
                       ("Fried Banana", "Snacks", 15, 20),
                       ("Halo-Halo", "Snacks", 45, 8)]),
]


class Lanes:
    """One shop's waiting line: a Queue for normal orders, a Min-Heap for urgent ones."""

    def __init__(self):
        self.normal = Queue()
        self.urgent = MinHeap()


# The in-memory structures. init() fills them from the database.
_shops = None           # Hash Table: shop id -> shop dict (id, name, password_hash)
_lanes = None           # Hash Table: shop id -> Lanes
_menu = None            # Hash Table: item id -> item dict (every shop's items)
_orders = None          # BST: order number -> order dict (the record store, every shop)
_order_list = None      # the same order dicts as a list sorted by order number (binary search)
_carts = None           # Hash Table: "email|shop id" -> Cart
_next_order_no = 1


# ---------- STARTUP ----------

def init():
    """Create the database if needed, then load everything into the structures."""
    global _shops, _lanes, _menu, _orders, _order_list, _carts, _next_order_no
    db.create_tables()
    _prepare_shops()
    ensure_admin()

    _shops = HashTable()
    _lanes = HashTable()
    for shop in db.load_shops():
        _register_shop(shop)

    _menu = HashTable()
    for item in db.load_menu_items():
        item["price"] = _tidy(item["price"])
        _menu.put(item["id"], item)

    _orders = BST()
    _carts = HashTable()
    for order in db.load_orders():                     # oldest first
        order["total"] = _tidy(order["total"])
        for line in order["items"]:
            line["price"] = _tidy(line["price"])
            line["name"] = _menu.get(line["menu_item_id"])["name"]
        _orders.insert(order["order_no"], order)
        if order["status"] == "Pending" and _lanes.contains(order["shop_id"]):
            _enqueue_pending(order)

    _order_list = [order for _, order in _orders.inorder()]   # the BST hands them over sorted
    _next_order_no = db.get_max_order_no() + 1


def _prepare_shops():
    """Make sure at least one shop exists before the structures are loaded."""
    if db.load_shops():
        return
    password_hash = generate_password_hash(config.DEFAULT_SHOP_PASSWORD, method="pbkdf2:sha256")
    if db.has_unassigned_rows():                       # data from the old one-shop version
        shop_id = db.add_shop("Main Canteen", password_hash)
        db.assign_unassigned_rows(shop_id)
        return
    for name, items in SAMPLE_SHOPS:                   # brand new database: sample shops
        shop_id = db.add_shop(name, password_hash)
        for item in items:
            db.add_menu_item(shop_id, *item)


def ensure_admin():
    """Create the canteen manager account if none exists. Only the hash is stored."""
    if db.get_admin(config.ADMIN_USERNAME) is None:
        db.add_admin(
            config.ADMIN_USERNAME,
            generate_password_hash(config.ADMIN_PASSWORD, method="pbkdf2:sha256"),
        )


def check_admin(username, password):
    """The canteen manager login (the one that adds shops)."""
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


# ---------- SHOPS (Hash Table) ----------

def _register_shop(shop):
    _shops.put(shop["id"], {"id": shop["id"], "name": shop["name"],
                            "password_hash": shop["password_hash"]})
    _lanes.put(shop["id"], Lanes())


def _get_shop(shop_id):
    if not _shops.contains(shop_id):
        raise ValueError("That shop does not exist")
    return _shops.get(shop_id)


def get_shop(shop_id):
    """The public details of one shop (never the password hash)."""
    shop = _get_shop(shop_id)
    return {"id": shop["id"], "name": shop["name"]}


def list_shops():
    shops = [{"id": shop["id"], "name": shop["name"]} for _, shop in _shops.items()]
    return merge_sort(shops, "name")


def shop_cards():
    """The shops for the student page, each with how many items can be ordered right now."""
    cards = list_shops()
    for card in cards:
        card["item_count"] = sum(
            1 for _, item in _menu.items()
            if item["shop_id"] == card["id"] and item["is_available"] and item["stock"] > 0
        )
    return cards


def _check_new_password(password):
    password = str(password)
    if not MIN_PASSWORD_LENGTH <= len(password) <= 100:
        raise ValueError(f"Password must be {MIN_PASSWORD_LENGTH} to 100 characters")
    return generate_password_hash(password, method="pbkdf2:sha256")


def _clean_shop_name(name, own_id=None):
    """Tidy the name and make sure no other shop already uses it (any capitalization)."""
    name = " ".join(str(name).split())                 # trim and collapse extra spaces
    if not 2 <= len(name) <= 40:
        raise ValueError("Shop name must be 2 to 40 characters")
    for shop_id, shop in _shops.items():
        if shop_id != own_id and shop["name"].lower() == name.lower():
            raise ValueError("A shop with that name already exists")
    return name


def add_shop(name, password):
    """Create a shop and its login account in one step. Returns the new shop id."""
    name = _clean_shop_name(name)
    password_hash = _check_new_password(password)
    try:
        shop_id = db.add_shop(name, password_hash)     # save first
    except sqlite3.IntegrityError:
        raise ValueError("A shop with that name already exists")
    _register_shop({"id": shop_id, "name": name, "password_hash": password_hash})
    return shop_id


def rename_shop(shop_id, new_name):
    shop = _get_shop(shop_id)
    new_name = _clean_shop_name(new_name, own_id=shop_id)   # its own old name does not count
    try:
        db.rename_shop(shop_id, new_name)              # save first
    except sqlite3.IntegrityError:
        raise ValueError("A shop with that name already exists")
    shop["name"] = new_name


def reset_shop_password(shop_id, new_password):
    shop = _get_shop(shop_id)
    password_hash = _check_new_password(new_password)
    db.update_shop_password(shop_id, password_hash)    # save first
    shop["password_hash"] = password_hash

def delete_shop(shop_id):
    """Delete a shop with its login, its menu and its order history."""
    global _orders, _order_list
    _get_shop(shop_id)
    if len(list_shops()) == 1:
        raise ValueError("You cannot delete the last shop")
    open_orders = [o for o in _order_list if o["shop_id"] == shop_id and o["status"] != "Completed"]
    if open_orders:
        raise ValueError(f"Finish or complete its {len(open_orders)} open order(s) first")
    db.delete_shop(shop_id)                            # save first, then clean up memory
    for item_id, item in _menu.items():
        if item["shop_id"] == shop_id:
            _menu.remove(item_id)
    for key, _ in _carts.items():
        if key.endswith(f"|{shop_id}"):
            _carts.remove(key)
    _order_list = [o for o in _order_list if o["shop_id"] != shop_id]
    _orders = BST()                                    # the BST has no delete, so rebuild it
    for order in _order_list:
        _orders.insert(order["order_no"], order)
    _shops.remove(shop_id)
    _lanes.remove(shop_id)

def check_shop_login(shop_id, password):
    if not _shops.contains(shop_id):
        return False
    return check_password_hash(_shops.get(shop_id)["password_hash"], password)
   
# ---------- SCHEDULING (one Queue and one Min-Heap per shop) ----------

def _enqueue_pending(order):
    lanes = _lanes.get(order["shop_id"])
    if order["priority"] == 0:
        lanes.urgent.push((0, order["order_no"]))      # urgent lane
    else:
        lanes.normal.enqueue(order["order_no"])        # normal lane


def _is_pending(order_no):
    index = binary_search(_order_list, order_no)
    return index != -1 and _order_list[index]["status"] == "Pending"


def _next_to_serve(shop_id):
    """Order number this shop should serve next, or None. Urgent lane first, then the queue.
    Orders that are no longer Pending are thrown away when they reach the front
    (lazy deletion), so we never have to remove from the middle of a queue."""
    lanes = _lanes.get(shop_id)
    while not lanes.urgent.is_empty():
        order_no = lanes.urgent.peek()[1]
        if _is_pending(order_no):
            return order_no
        lanes.urgent.pop()
    while not lanes.normal.is_empty():
        order_no = lanes.normal.peek()
        if _is_pending(order_no):
            return order_no
        lanes.normal.dequeue()
    return None


# ---------- MENU (Hash Table) ----------

def _get_item(shop_id, item_id):
    """The item, but only if it belongs to this shop (a shop can never touch another's menu)."""
    if not _menu.contains(item_id) or _menu.get(item_id)["shop_id"] != shop_id:
        raise ValueError("That menu item does not exist")
    return _menu.get(item_id)


def get_menu(shop_id, search="", sort_by="name", include_hidden=False):
    search = search.strip().lower()
    if sort_by not in ("name", "price"):
        sort_by = "name"
    items = []
    for _, item in _menu.items():
        if item["shop_id"] != shop_id:
            continue
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


def add_menu_item(shop_id, name, category, price, stock):
    _get_shop(shop_id)
    name, category, price, stock = _clean_menu_input(name, category, price, stock)
    item_id = db.add_menu_item(shop_id, name, category, price, stock)      # save first
    _menu.put(item_id, {"id": item_id, "shop_id": shop_id, "name": name, "category": category,
                        "price": price, "stock": stock, "is_available": 1})
    return item_id


def update_menu_item(shop_id, item_id, name, category, price, stock, available=None):
    """available=None keeps the current setting; True or False shows or hides the item."""
    item = _get_item(shop_id, item_id)
    name, category, price, stock = _clean_menu_input(name, category, price, stock)
    is_available = item["is_available"] if available is None else (1 if available else 0)
    db.update_menu_item(item_id, name, category, price, stock, is_available)
    item.update(name=name, category=category, price=price, stock=stock,
                is_available=is_available)


def remove_menu_item(shop_id, item_id):
    """Delete the item. If past orders use it, hide it instead. Returns what happened."""
    item = _get_item(shop_id, item_id)
    try:
        db.delete_menu_item(item_id)
    except sqlite3.IntegrityError:                     # old orders still point to it
        db.update_menu_item(item_id, item["name"], item["category"],
                            item["price"], item["stock"], 0)
        item["is_available"] = 0
        return "hidden"
    _menu.remove(item_id)
    return "deleted"


# ---------- CART (Hash Table + Stack), one cart per student per shop ----------

class Cart:
    """One cart. Hash Table = item id -> quantity. Stack = undo history."""

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


def _cart_key(email, shop_id):
    return f"{email}|{shop_id}"


def _get_cart(email, shop_id):
    key = _cart_key(email, shop_id)
    if not _carts.contains(key):
        _carts.put(key, Cart())
    return _carts.get(key)


def cart_add(email, shop_id, item_id):
    item = _get_item(shop_id, item_id)
    cart = _get_cart(email, shop_id)
    new_qty = cart.qty(item_id) + 1
    if not item["is_available"] or item["stock"] <= 0:
        raise ValueError(f'{item["name"]} is out of stock')
    if new_qty > item["stock"]:
        raise ValueError(f'Only {item["stock"]} {item["name"]} left')
    if new_qty > MAX_QTY_PER_ITEM:
        raise ValueError(f"You can order at most {MAX_QTY_PER_ITEM} of one item")
    cart.set_qty(item_id, new_qty)


def cart_decrease(email, shop_id, item_id):
    cart = _get_cart(email, shop_id)
    qty = cart.qty(item_id)
    if qty == 0:
        raise ValueError("That item is not in your cart")
    cart.set_qty(item_id, qty - 1)


def cart_remove(email, shop_id, item_id):
    cart = _get_cart(email, shop_id)
    if cart.qty(item_id) == 0:
        raise ValueError("That item is not in your cart")
    cart.set_qty(item_id, 0)


def cart_undo(email, shop_id):
    try:
        _get_cart(email, shop_id).undo()
    except IndexError:
        raise ValueError("Nothing to undo")


def cart_view(email, shop_id):
    """Returns (lines, total). Each line: id, name, price, qty."""
    cart = _get_cart(email, shop_id)
    lines = []
    total = 0
    for item_id, qty in cart.lines.items():
        if not _menu.contains(item_id):                # the shop deleted it meanwhile
            cart._apply(item_id, 0)
            continue
        item = _menu.get(item_id)
        lines.append({"id": item_id, "name": item["name"], "price": item["price"], "qty": qty})
        total += item["price"] * qty
    return merge_sort(lines, "id"), total


# ---------- ORDERS (Queue + Min-Heap per shop, BST, binary search) ----------

def _check_table_no(table_no):
    table_no = str(table_no).strip()
    if not table_no.isdecimal() or not 1 <= int(table_no) <= MAX_TABLE_NO:
        raise ValueError(f"Table number must be from 1 to {MAX_TABLE_NO}")
    return str(int(table_no))


def place_order(email, shop_id, table_no, urgent=False):
    """Turn this student's cart for this shop into an order. Returns the new order number."""
    global _next_order_no
    _get_shop(shop_id)
    table_no = _check_table_no(table_no)
    key = _cart_key(email, shop_id)
    if not _carts.contains(key) or _carts.get(key).is_empty():
        raise ValueError("Your cart is empty")
    cart = _carts.get(key)

    lines = []                                         # re-check stock at the last moment
    total = 0
    for item_id, qty in cart.lines.items():
        item = _get_item(shop_id, item_id)
        if not item["is_available"] or qty > item["stock"]:
            raise ValueError(f'Not enough stock for {item["name"]}')
        lines.append({"menu_item_id": item_id, "name": item["name"],
                      "quantity": qty, "price": item["price"]})
        total += item["price"] * qty

    order_no = _next_order_no
    priority = 0 if urgent else 1
    created_at = db.save_order(order_no, table_no, "Pending", priority, total, lines,
                               email, shop_id)

    order = {"order_no": order_no, "table_no": table_no, "status": "Pending",
             "priority": priority, "total": total, "created_at": created_at,
             "items": lines, "customer_email": email, "shop_id": shop_id}
    _orders.insert(order_no, order)                    # BST: store the record
    _order_list.append(order)                          # still sorted: new numbers are the biggest
    _enqueue_pending(order)                            # this shop's Queue or Min-Heap

    for line in lines:                                 # take the stock
        item = _menu.get(line["menu_item_id"])
        item["stock"] -= line["quantity"]
        db.update_stock(item["id"], item["stock"])

    _next_order_no += 1
    _carts.remove(key)
    return order_no


def update_status(shop_id, order_no, new_status):
    order = _find_record(order_no)
    if order["shop_id"] != shop_id:                    # same message: do not reveal other shops' orders
        raise ValueError(f"Order #{order_no} not found")
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
    shop = _shops.get(order["shop_id"]) if _shops.contains(order["shop_id"]) else None
    return {
        "order_no": order["order_no"],
        "table_no": order["table_no"],
        "items_text": ", ".join(parts),
        "status": order["status"],
        "total": order["total"],
        "minutes_waiting": waiting,
        "urgent": order["priority"] == 0 or waiting >= URGENT_MINUTES,
        "customer_email": order.get("customer_email", ""),
        "shop_id": order["shop_id"],
        "shop_name": shop["name"] if shop else "",
    }


def find_order(order_no):
    index = binary_search(_order_list, order_no)
    return _order_view(_order_list[index]) if index != -1 else None


def find_shop_order(shop_id, order_no):
    """Like find_order, but only for an order that belongs to this shop."""
    order = find_order(order_no)
    return order if order and order["shop_id"] == shop_id else None


def my_orders(email, limit=None):
    """One student's orders from every shop, newest first."""
    mine = [order for order in _order_list if order["customer_email"] == email]
    views = [_order_view(order) for order in reversed(mine)]
    return views if limit is None else views[:limit]


def all_orders(shop_id):
    return [_order_view(order) for _, order in _orders.inorder() if order["shop_id"] == shop_id]


def dashboard(shop_id):
    """Returns (next order to serve or None, list of active orders) for one shop."""
    next_no = _next_to_serve(shop_id)
    next_view = find_order(next_no) if next_no is not None else None
    active = [_order_view(order) for _, order in _orders.inorder()
              if order["shop_id"] == shop_id and order["status"] in ("Pending", "Preparing", "Ready")]
    return next_view, active


def sales_report(shop_id, sort_by="order_no"):
    """Returns (completed orders, total sales, sort used) for one shop."""
    if sort_by not in ("order_no", "total"):
        sort_by = "order_no"
    completed = [_order_view(order) for _, order in _orders.inorder()
                 if order["shop_id"] == shop_id and order["status"] == "Completed"]
    completed = merge_sort(completed, sort_by)
    total_sales = sum(order["total"] for order in completed)
    return completed, total_sales, sort_by
