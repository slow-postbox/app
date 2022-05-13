from flask import Blueprint
from flask import render_template

from app import db
from app.models import User
from app.models import LoginHistory
from app.models import Mail
from app.utils import login_required

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@bp.get("")
@login_required
def index(user: User):
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
@login_required
def history(user: User):
    return


@bp.get("/quit-service")
@login_required
def quit_service(user: User):
    return
