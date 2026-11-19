from flask import Flask, render_template, request
import config
from Back_End import service
from Back_End.routes.costumer import customer_bp

app = Flask(
    __name__,
    template_folder="Front_End/templates",
    static_folder="Front_End/static",
)
app.secret_key = config.SECRET_KEY

service.init()
app.register_blueprint(customer_bp)

#route for costumer login dashboard so it can find from base html
@app.route("/")
@app.route("/login")
def login():
    return render_template("costumer/login.html")

#route for costumer login dashboard so it can find from base html
@app.route("/admin/login")
def admin_login():
    return render_template("admin/login.html")


#menu items for costumer menu page
menu_items = [
    {"id": 1, "name": "Chicken Adobo", "price": 60, "stock": 10},
    {"id": 2, "name": "Pancit Canton", "price": 35, "stock": 5},
    {"id": 3, "name": "Iced Tea", "price": 20, "stock": 0},
]


#admin dashboard page
pending_orders = [
    {"order_no": 42, "table_no": 5, "items": "2x Chicken Adobo", "status": "Pending", "minutes_waiting": 6},
    {"order_no": 43, "table_no": 2, "items": "1x Pancit Canton", "status": "Pending", "minutes_waiting": 4},
    {"order_no": 41, "table_no": 7, "items": "3x Iced Tea", "status": "Preparing", "minutes_waiting": 12},
]

@app.route("/admin/dashboard")
def admin_dashboard():
    next_order = pending_orders[0] if pending_orders else None
    return render_template(
        "admin/dashboard.html",
        orders=pending_orders,
        next_order=next_order,
    )


all_orders = [
    {"order_no": 38, "table_no": 3, "items": "1x Iced Tea", "status": "Completed", "total": 20},
    {"order_no": 39, "table_no": 1, "items": "2x Pancit Canton", "status": "Completed", "total": 70},
    {"order_no": 40, "table_no": 6, "items": "1x Chicken Adobo", "status": "Completed", "total": 60},
    {"order_no": 41, "table_no": 7, "items": "3x Iced Tea", "status": "Preparing", "total": 60},
    {"order_no": 42, "table_no": 5, "items": "2x Chicken Adobo", "status": "Pending", "total": 120},
]


#alll of the orders page for admin to view all orders and search for specific order by order number
@app.route("/admin/orders")
def admin_orders():
    search = request.args.get("order_id", "").strip()
    orders_to_show = all_orders
    message = ""

    if search:
        if not search.isdigit():
            orders_to_show = []
            message = "Please enter a valid order number."
        else:
            orders_to_show = []
            for order in all_orders:        # linear search
                if order["order_no"] == int(search):
                    orders_to_show.append(order)
                    break
            if not orders_to_show:
                message = "No order found with that number."

    return render_template("admin/orders.html", orders=orders_to_show, message=message)

#menu management page for admin 
@app.route("/admin/menu")
def admin_menu():
    return render_template("admin/menu_manage.html", items=menu_items)

#sales report

@app.route("/admin/reports")
def admin_reports():
    sort_by = request.args.get("sort", "order_no")
    if sort_by not in ("order_no", "total"):
        sort_by = "order_no"

    completed = [o for o in all_orders if o["status"] == "Completed"]
    completed = sorted(completed, key=lambda o: o[sort_by])  # placeholder sort

    total_sales = sum(o["total"] for o in completed)

    return render_template(
        "admin/reports.html",
        orders=completed,
        total_sales=total_sales,
        sort_by=sort_by,
    )

if __name__ == "__main__":
    app.run(debug=True)