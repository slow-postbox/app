from flask import Blueprint
from flask import session
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template

from app import db
from app.models import User
from app.models import LoginHistory
from app.models import Mail
from app.models import PasswordReset
from app.models import UserLock
from app.utils import get_error_message
from app.utils import set_error_message
from app.utils import login_required
from app.utils import admin_only

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
        reset=user.password.startswith( "social-login-account")
    )


@bp.get("/reset")
@login_required
def reset_history(user: User):
    if user.password.startswith("social-login-account"):
        return redirect(url_for("dashboard.index"))

    pws = PasswordReset.query.filter_by(
        owner_id=user.id,
    ).order_by(
        PasswordReset.id.desc()
    ).all()

    return render_template(
        "dashboard/reset.html",
        pws=pws,
    )


@bp.get("/user-lock")
@login_required
@admin_only
def lock(user: User):
    return render_template(
        "dashboard/lock.html",
        error=get_error_message(),
        message=get_error_message("message"),
    )


@bp.post("/user-lock")
@login_required
@admin_only
def lock_post(user: User):
    target = User.query.filter_by(
        email=request.form.get("email").strip()
    ).first()

    if target is None:
        error_id = set_error_message(message="등록된 계정이 아닙니다.")
        return redirect(url_for("dashboard.lock", error=error_id))

    user_lock = UserLock()
    user_lock.owner_id = target.id
    user_lock.reason = request.form.get("reason").strip()

    if len(user_lock.reason) == 0:
        user_lock.reason = "* 등록된 사유가 없습니다."

    db.session.add(user_lock)
    db.session.commit()

    message_id = set_error_message(message="해당 계정이 잠겼습니다.")
    return redirect(url_for("dashboard.lock", message=message_id))


@bp.get("/quit-service")
@login_required
def quit_service(user: User):
    emoji = {
        True: "✔️",
        False: "❌"
    }

    mail = Mail.query.filter_by(
        owner_id=user.id
    ).count()

    protect = UserLock.query.filter_by(
        owner_id=user.id
    ).all()

    return render_template(
        "dashboard/quit.html",
        error=get_error_message(),
        admin=emoji.get(not user.admin),
        mail=emoji.get(mail == 0),
        protect=emoji.get(len(protect) == 0),
        protects=protect,
    )


@bp.post("/quit-service")
@login_required
def quit_service_post(user: User):
    def to(message: str):
        error_id = set_error_message(message=message)
        return redirect(url_for("dashboard.quit_service", error=error_id))

    if user.admin:
        return to(message="관리자는 탈퇴 할 수 없습니다.")

    if Mail.query.filter_by(
        owner_id=user.id
    ).count() != 0:
        return to(message="작성한 편지가 있어서 해당 요청을 승인 할 수 없습니다.")

    if UserLock.query.filter_by(
        owner_id=user.id
    ).count() != 0:
        return to(message="계정 잠금 요청에 의해 해당 요청을 승인 할 수 없습니다.")

    LoginHistory.query.filter_by(
        owner_id=user.id
    ).delete()
    PasswordReset.query.filter_by(
        owner_id=user.id
    ).delete()

    db.session.delete(user)
    db.session.commit()

    for key in list(session.keys()):
        del session[key]

    return render_template(
        "dashboard/quit-next.html"
    )
