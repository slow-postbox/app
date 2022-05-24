from flask import Blueprint
from flask import g
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template

from app import db
from app.models import User
from app.models import PrivacyPolicy
from app.utils import get_error_message
from app.utils import set_error_message
from app.utils import login_required
from app.utils import admin_only
from app.utils import fetch_privacy

bp = Blueprint("privacy", __name__, url_prefix="/privacy")


@bp.get("")
def latest():
    privacy = PrivacyPolicy.query.order_by(
        PrivacyPolicy.id.desc()
    ).first()

    if privacy is None:
        return redirect(url_for("privacy.create_new"))

    return render_template(
        "privacy/detail.html",
        error=get_error_message(),
        message=get_error_message("message"),
        privacy=privacy,
        pp=PrivacyPolicy.query.order_by(
            PrivacyPolicy.id.desc()
        ).with_entities(
            PrivacyPolicy.id,
            PrivacyPolicy.creation_date,
        ).all(),
    )


@bp.get("/<int:privacy_id>")
@fetch_privacy
def detail(privacy: PrivacyPolicy, privacy_id: int):
    return render_template(
        "privacy/detail.html",
        error=get_error_message(),
        privacy=privacy,
        pp=PrivacyPolicy.query.order_by(
            PrivacyPolicy.id.desc()
        ).with_entities(
            PrivacyPolicy.id,
            PrivacyPolicy.creation_date,
        ).all()
    )


@bp.get("/create-new")
@login_required
@admin_only
def create_new(user: User):
    g.editor_css = True
    return render_template(
        "privacy/create-new.html",
        error=get_error_message()
    )


@bp.post("/create-new")
@login_required
@admin_only
def create_new_post(user: User):
    content = request.form.get("content").strip()
    if len(content) == 0:
        error_id = set_error_message("본문 내용이 비었습니다.")
        return redirect(url_for("privacy.create_new", error=error_id))

    privacy = PrivacyPolicy()
    privacy.content = content

    db.session.add(privacy)
    db.session.commit()

    return redirect(url_for("privacy.detail", privacy_id=privacy.id))


@bp.get("/edit/<int:privacy_id>")
@login_required
@admin_only
@fetch_privacy
def edit(privacy: PrivacyPolicy, privacy_id: int, user: User):
    g.editor_css = True
    return render_template(
        "privacy/edit.html",
        privacy=privacy,
        error=get_error_message()
    )


@bp.post("/edit/<int:privacy_id>")
@login_required
@admin_only
@fetch_privacy
def edit_post(privacy: PrivacyPolicy, privacy_id: int, user: User):
    content = request.form.get("content").strip()
    if len(content) == 0:
        error_id = set_error_message("본문 내용이 비었습니다.")
        return redirect(url_for("privacy.edit", privacy_id=privacy_id, error=error_id))

    privacy.content = content
    db.session.commit()

    return redirect(url_for("privacy.edit", privacy_id=privacy_id))


@bp.get("/delete/<int:privacy_id>")
@login_required
@admin_only
def delete(privacy_id: int, user: User):
    PrivacyPolicy.query.filter_by(
        id=privacy_id
    ).delete()

    db.session.commit()
    return redirect(url_for("privacy.latest",
                            message=set_error_message("해당 개인정보 처리방침을 삭제했습니다.")))
