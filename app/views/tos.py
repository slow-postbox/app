from flask import Blueprint
from flask import g
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template

from app import db
from app.models import User
from app.models import TermsOfService
from app.utils import get_error_message
from app.utils import set_error_message
from app.utils import login_required
from app.utils import admin_only
from app.utils import fetch_tos

bp = Blueprint("tos", __name__, url_prefix="/tos")


@bp.get("")
def latest():
    tos = TermsOfService.query.order_by(
        TermsOfService.id.desc()
    ).first()

    if tos is None:
        return redirect(url_for("tos.create_new"))

    return render_template(
        "tos/detail.html",
        error=get_error_message(),
        tos=tos,
        toss=TermsOfService.query.order_by(
            TermsOfService.id.desc()
        ).with_entities(
            TermsOfService.id,
            TermsOfService.creation_date,
        ).all(),
    )


@bp.get("/<int:tos_id>")
@fetch_tos
def detail(tos: TermsOfService, tos_id: int):
    return render_template(
        "tos/detail.html",
        error=get_error_message(),
        tos=tos,
        toss=TermsOfService.query.order_by(
            TermsOfService.id.desc()
        ).with_entities(
            TermsOfService.id,
            TermsOfService.creation_date,
        ).all()
    )


@bp.get("/create-new")
@login_required
@admin_only
def create_new(user: User):
    g.editor_css = True
    return render_template(
        "tos/create-new.html",
        error=get_error_message()
    )


@bp.post("/create-new")
@login_required
@admin_only
def create_new_post(user: User):
    content = request.form.get("content").strip()
    if len(content) == 0:
        error_id = set_error_message("본문 내용이 비었습니다.")
        return redirect(url_for("tos.create_new", error=error_id))

    tos = TermsOfService()
    tos.content = content

    db.session.add(tos)
    db.session.commit()

    return redirect(url_for("tos.detail", tos_id=tos.id))


@bp.get("/edit/<int:tos_id>")
@login_required
@admin_only
@fetch_tos
def edit(tos: TermsOfService, tos_id: int, user: User):
    g.editor_css = True
    return render_template(
        "tos/edit.html",
        tos=tos,
        error=get_error_message()
    )


@bp.post("/edit/<int:tos_id>")
@login_required
@admin_only
@fetch_tos
def edit_post(tos: TermsOfService, tos_id: int, user: User):
    content = request.form.get("content").strip()
    if len(content) == 0:
        error_id = set_error_message("본문 내용이 비었습니다.")
        return redirect(url_for("tos.edit", tos_id=tos_id, error=error_id))

    tos.content = content
    db.session.commit()

    return redirect(url_for("tos.edit", tos_id=tos_id))
