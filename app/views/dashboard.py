from flask import Blueprint
from flask import session
from flask import redirect
from flask import url_for
from flask import render_template

from app import db
from app.models import User
from app.models import LoginHistory
from app.models import Mail

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@bp.get("")
def index():
    if 'user' not in session:
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(
        id=session['user']['user_id']
    ).first()

    if user is None:
        del session['user']
        return redirect(url_for("auth.sign_up", error="삭제된 계정입니다."))

    mails = Mail.query.filter_by(
        owner_id=user.id
    ).all()

    return render_template(
        "dashboard/index.html",
        user=user,
        mails=mails,
        mail_count=len(mails),
    )


@bp.get("/history")
def history():
    return


@bp.get("/quit-service")
def quit_service():
    return
