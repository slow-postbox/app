from flask import Blueprint
from flask import render_template

from app import db
from app.models import User
from app.models import LoginHistory
from app.models import Mail
from app.utils import get_error_message
from app.utils import login_required

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@bp.get("")
@login_required
def index(user: User):
    mails = Mail.query.filter_by(
        owner_id=user.id
    ).order_by(
        Mail.id.desc()
    ).all()

    return render_template(
        "dashboard/index.html",
        user=user,
        mails=mails,
        mail_count=len(mails),
        error=get_error_message(),
        message=get_error_message("message")
    )


@bp.get("/history")
@login_required
def history(user: User):
    login_history = LoginHistory.query.filter_by(
        owner_id=user.id,
    ).order_by(
        LoginHistory.id.desc()
    ).all()

    return render_template(
        "dashboard/history.html",
        histories=login_history,
    )


@bp.get("/quit-service")
@login_required
def quit_service(user: User):
    return
