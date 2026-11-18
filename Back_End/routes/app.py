from flask import Flask, render_template

app = Flask(
    __name__,
    template_folder="Front_End/templates",
    static_folder="Front_End/static",
)

#route for costumer login dashboard so it can find from base html
@app.route("/")
@app.route("/login")
def login():
    return render_template("costumer/login.html")

#route for costumer login dashboard so it can find from base html
@app.route("/admin/login")
def admin_login():
    return render_template("admin/login.html")

if __name__ == "__main__":
    app.run(debug=True)

#menu items for costumer menu page
menu_items = [
    {"id": 1, "name": "Chicken Adobo", "price": 60, "stock": 10},
    {"id": 2, "name": "Pancit Canton", "price": 35, "stock": 5},
    {"id": 3, "name": "Iced Tea", "price": 20, "stock": 0},
]

@app.route("/menu")
def menu():
    return render_template("costumer/menu.html", items=menu_items)