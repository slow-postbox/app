from flask import Blueprint
from flask import render_template

bp = Blueprint("index", __name__, url_prefix="/")


@bp.get("")
def index():
    return render_template(
        "index/index.html"
    )
