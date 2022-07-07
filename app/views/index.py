from flask import Blueprint
from flask import render_template

from app.utils import login_block

bp = Blueprint("index", __name__, url_prefix="/")


@bp.get("")
@login_block
def index():
    return render_template(
        "index/index.html"
    )
