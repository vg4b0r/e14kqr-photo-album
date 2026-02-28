from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from . import db
from .models import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.get("/register")
def register_form():
    return render_template("register.html")

@auth_bp.post("/register")
def register():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Email és jelszó kötelező.")
        return redirect(url_for("auth.register_form"))

    if User.query.filter_by(email=email).first():
        flash("Ez az email már regisztrálva van.")
        return redirect(url_for("auth.register_form"))

    u = User(email=email)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    flash("Sikeres regisztráció, most jelentkezz be.")
    return redirect(url_for("auth.login"))

@auth_bp.get("/login")
def login():
    return render_template("login.html")

@auth_bp.post("/login")
def login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    u = User.query.filter_by(email=email).first()

    if not u or not u.check_password(password):
        flash("Hibás belépési adatok.")
        return redirect(url_for("auth.login"))

    login_user(u)
    return redirect(url_for("photos.index"))

@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))