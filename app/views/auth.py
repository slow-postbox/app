from flask import Blueprint
from flask import request
from flask import render_template

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.get("/login")
def login():
    return render_template(
        "auth/login.html",
    )


@bp.post("/login")
def login_post():
    return


@bp.get("/sign-up")
def sign_up():
    return render_template(
        "auth/sign-up.html",
    )


@bp.post("/sign-up")
def sign_up_post():
    return


@bp.get("/password-reset")
def password_reset():
    return render_template(
        "auth/password-reset.html"
    )


@bp.post("/password-reset")
def password_reset_post():
    return
