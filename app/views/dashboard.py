from flask import Blueprint
from flask import session
from flask import redirect
from flask import url_for

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@bp.get("")
def index():
    if 'user' not in session:
        return redirect(url_for("auth.login"))

    return "WIP"
