from flask import Blueprint
from flask import redirect
from flask import url_for

import post

bp = Blueprint("post", __name__, url_prefix="/post")

for p in post.__all__:
    bp.register_blueprint(getattr(getattr(post, p), "bp"))


@bp.get("")
def back_to_dashboard():
    return redirect(url_for("dashboard.index"))
