from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_user, logout_user
from models import User

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.get("admin")
        login_user(user)
        return redirect(url_for("views.dashboard"))
    return render_template("login.html")

@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
