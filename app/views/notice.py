from flask import Blueprint
from flask import g
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template

from app import db
from app.models import User
from app.models import Notice
from app.utils import login_required
from app.utils import admin_only
from app.utils import fetch_notice
from app.utils import get_error_message
from app.utils import set_error_message

bp = Blueprint("notice", __name__, url_prefix="/notice")


@bp.get("")
def show_list():
    notices = Notice.query.order_by(
        Notice.id.desc()
    ).all()

    return render_template(
        "notice/show_list.html",
        notices=notices
    )


@bp.get("/<int:notice_id>")
@fetch_notice
def detail(notice: Notice, notice_id: int):
    return render_template(
        "notice/detail.html",
        notice=notice
    )


@bp.get("/create-new")
@login_required
@admin_only
def create_new(user: User):
    g.editor_css = True
    return render_template(
        "notice/create-new.html",
        error=get_error_message()
    )


@bp.post("/create-new")
@login_required
@admin_only
def create_new_post(user: User):
    def error(message: str):
        error_id = set_error_message(message=message)
        return redirect(url_for("notice.create_new", error=error_id))

    title = request.form.get("title", "").strip()
    if len(title) == 0:
        return error("공지 제목을 설정해야 합니다.")

    content = request.form.get("content", "").strip()
    if len(content) == 0:
        return error("공지 내용을 설정해야 합니다.")

    notice = Notice()
    notice.title = title
    notice.content = content

    db.session.add(notice)
    db.session.commit()

    return redirect(url_for("notice.edit", notice_id=notice.id))


@bp.get("/edit/<int:notice_id>")
@login_required
@admin_only
@fetch_notice
def edit(user: User, notice: Notice, notice_id: int):
    g.editor_css = True
    return render_template(
        "notice/edit.html",
        error=get_error_message(),
        notice=notice
    )


@bp.post("/edit/<int:notice_id>")
@login_required
@admin_only
@fetch_notice
def edit_post(user: User, notice: Notice, notice_id: int):
    title = request.form.get("title", "").strip()
    if len(title) != 0:
        notice.title = title

    content = request.form.get("content", "").strip()
    if len(content) != 0:
        notice.content = content

    db.session.commit()

    return redirect(url_for("notice.edit", notice_id=notice_id))
