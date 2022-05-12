from flask import Blueprint

bp = Blueprint("write", __name__, url_prefix="/write")


@bp.get("/create-new")
def create_new():
    return "create_new"


@bp.post("/create-new")
def create_new_post():
    return "create_new"


@bp.get("/<int:mail_id>")
def edit(mail_id: int):
    return f"{mail_id}"


@bp.post("/<int:mail_id>")
def edit_post(mail_id: int):
    return f"{mail_id}"
