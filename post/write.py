from datetime import datetime
from datetime import timedelta

from flask import Blueprint
from flask import g
from flask import session
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template

bp = Blueprint("write", __name__, url_prefix="/write")


@bp.get("/create-new")
def create_new():
    g.editor_css = True
    return render_template(
        "post/write/create-new.html",
        date=(datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    )


@bp.post("/create-new")
def create_new_post():
    return "create_new"


@bp.get("/<int:mail_id>")
def edit(mail_id: int):
    g.editor_css = True
    return render_template(
        "post/write/edit.html",
    )


@bp.post("/<int:mail_id>")
def edit_post(mail_id: int):
    return f"{mail_id}"
