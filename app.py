from flask import Flask, render_template

import config
from Back_End import service
from Back_End.routes.admin import admin_bp
from Back_End.routes.costumer import customer_bp

app = Flask(
    __name__,
    template_folder="Front_End/templates",
    static_folder="Front_End/static",
)
app.secret_key = config.SECRET_KEY

service.init()                      # load the database into the data structures
app.register_blueprint(customer_bp)
app.register_blueprint(admin_bp)


@app.route("/")
@app.route("/login")
def login():
    return render_template("costumer/login.html")


if __name__ == "__main__":
    app.run(debug=True)