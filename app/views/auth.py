from flask import Blueprint
from flask import session
from flask import redirect
from flask import render_template

from app.utils import get_error_message

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.get("/error")
def error():
    return render_template(
        "auth/error.html",
        error=get_error_message()
    )


@bp.get("/login")
def login():
    return render_template(
        "kakao/login.html"
    )


@bp.get("/logout")
def logout():
    for key in list(session.keys()):
        del session[key]

    return redirect("/?logout")
