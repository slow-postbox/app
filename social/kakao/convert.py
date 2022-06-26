from flask import Blueprint

bp = Blueprint("convert", __name__, url_prefix="/convert")


@bp.get("")
def index():
    return


@bp.post("")
def index_post():
    return
