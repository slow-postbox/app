from logging import getLogger

from flask import Blueprint
from flask import redirect
from flask import url_for
from flask import render_template

from app import db
from app.models import User
from app.models import Mail
from app.utils import get_today
from app.utils import set_error_message
from app.utils import login_after
from app.utils import login_required
from mail.crypto import decrypt_mail

bp = Blueprint("read", __name__, url_prefix="/read")
logger = getLogger()


@bp.get("/<int:mail_id>")
@login_after("mail.read.select")
@login_required
def detail(user: User, mail_id: int):
    mail = Mail.query.filter_by(
        id=mail_id,
        owner_id=user.id,
    ).first()

    if mail is None:
        error_id = set_error_message("해당 편지를 찾지 못했습니다.")
        return redirect(url_for("dashboard.index", error=error_id))

    if mail.lock is False:
        error_id = set_error_message(["해당 편지는 우체통에 들어가지 않았습니다."])
        return redirect(url_for("mail.write.edit", mail_id=mail_id, error=error_id))

    if mail.send_date > get_today():
        return redirect(url_for("mail.write.edit", mail_id=mail_id))

    if mail.read is False:
        mail.read = True
        db.session.commit()

    try:
        mail.content = decrypt_mail(
            owner_id=user.id,
            mail_id=mail_id,
            result=mail.content
        )
    except (ValueError, Exception) as e:
        logger.exception(e)
        error_id = set_error_message("메일을 불러오는데 오류가 발생했습니다.")
        return redirect(url_for("dashboard.index", error=error_id))

    return render_template(
        "mail/read/detail.html",
        mail=mail
    )


@bp.get("/select")
@login_after("mail.read.select")
@login_required
def select(user: User):
    mails = Mail.query.with_entities(
        Mail.id,
        Mail.title,
        Mail.creation_date,
    ).filter_by(
        owner_id=user.id,
        lock=True
    ).filter(
        Mail.send_date < get_today()
    ).all()

    # 읽을 수 있는 메일이 없다면
    if len(mails) == 0:
        message_id = set_error_message("읽을 수 있는 메일이 없습니다.")
        return redirect(url_for("dashboard.index", message=message_id))

    # 읽을 수 있는 메일이 1개만 있다면
    if len(mails) == 1:
        return redirect(url_for("mail.read.detail", mail_id=mails[0].id))

    return render_template(
        "mail/read/select.html",
        mails=mails
    )
