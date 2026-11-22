from flask import Flask, redirect, session, url_for

import config
from Back_End import service
from Back_End.routes.admin import admin_bp
from Back_End.routes.auth import auth_bp
from Back_End.routes.costumer import customer_bp

app = Flask(
    __name__,
    template_folder="Front_End/templates",
    static_folder="Front_End/static",
)
app.secret_key = config.SECRET_KEY
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

service.init()                      # load the database into the data structures
app.register_blueprint(auth_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(admin_bp)


@app.route("/")
def home():
    if session.get("student"):
        return redirect(url_for("customer.shops"))
    return redirect(url_for("auth.login"))


@app.errorhandler(404)
def not_found(error):
    return 'Page not found. <a href="/menu">Back to the menu</a>', 404


if __name__ == "__main__":
    app.run(debug=True)
