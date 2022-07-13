from datetime import datetime
from datetime import timedelta
from logging import getLogger

from flask import Blueprint
from flask import g
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template

from app import db
from app.models import User
from app.models import Mail
from app.utils import login_after
from app.utils import login_required
from app.utils import fetch_mail
from app.utils import create_csrf_token
from app.utils import verify_csrf_token
from app.utils import get_error_message
from app.utils import set_error_message
from mail.crypto import encrypt_mail
from mail.crypto import decrypt_mail
from mail.utils import delete_key_store
from mail.utils import check_user_lock

bp = Blueprint("write", __name__, url_prefix="/")
logger = getLogger()

# 최소 1주일
MIN_DAYS = 7
# 최대 1년하고 4주일
MAX_DAYS = 365 + timedelta(weeks=4).days
# 편지 개수 제한
MAIL_LIMIT = 20
# 발송 날짜 제한
SEND_LIMIT = 200


def check_date_limit(date: datetime) -> bool:
    count = Mail.query.filter_by(
        send_date=date
    ).count()

    # true : 제한 걸림 요청 거부
    return count > SEND_LIMIT


@bp.get("/create-new")
@login_after('mail.write.create_new')
@login_required
def create_new(user: User):
    if Mail.query.filter_by(
        owner_id=user.id
    ).count() >= MAIL_LIMIT:
        return render_template(
            "mail/write/limit.html",
            limit=MAIL_LIMIT
        )

    g.editor_css = True
    return render_template(
        "mail/write/create-new.html",
        date=(datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
        error=get_error_message(),
        csrf=create_csrf_token()
    )


@bp.post("/create-new")
@login_after('mail.write.create_new')
@login_required
def create_new_post(user: User):
    if Mail.query.filter_by(
        owner_id=user.id
    ).count() >= MAIL_LIMIT:
        return render_template(
            "mail/write/limit.html",
            limit=MAIL_LIMIT
        )

    def error(message):
        error_id = set_error_message(message=message)
        return redirect(url_for("mail.write.create_new", error=error_id))

    try:
        csrf = request.form['csrf']
        if not verify_csrf_token(csrf_token=csrf):
            return error("CSRF 토큰이 올바르지 않습니다.")
    except KeyError:
        return error("CSRF 토큰이 없습니다.")

    try:
        content = request.form['content']

        if len(content) > 20000:
            return error("본문이 20000자 보다 길 수 없습니다.")
    except KeyError:
        return error("편지 본문을 전달 받지 못 했습니다.")

    try:
        # 편지를 보낼 날짜를 불러옴
        send_date = datetime.strptime(request.form['date'], "%Y-%m-%d")

        # 하루 200통 체크
        if check_date_limit(date=send_date):
            return error(f"해당 날짜에 보내는 편지가 <b>{SEND_LIMIT}</b>통이 넘어 해당 날짜를 선택 할 수 없습니다.")

        # 같은 요일에 보내는 편지를 작성한 적이 있다면 거부
        test = Mail.query.filter_by(
            owner_id=user.id,
            send_date=send_date
        ).first()

        if test is not None:
            date = send_date.strftime("%Y년 %m월 %d일")
            return error(f"<b>{date}</b>로 보내는 편지가 이미 있습니다.")

        # 기준 날짜 = 오늘 날짜
        days = (send_date - datetime.today()).days + 1

        if days < MIN_DAYS:
            # 보낼 날짜가 너무 가까움
            raise ValueError

        if days > MAX_DAYS:
            # 보낼 날짜가 너무 멈
            raise ValueError
    except (KeyError, ValueError):
        # 기본 값은 작성일로부터 1년뒤
        send_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")

    mail = Mail()
    mail.owner_id = user.id
    mail.send_date = send_date
    mail.title = request.form.get("title", "제목 없는 편지").strip()[:100]
    mail.content = content
    mail.lock = True if request.form.get("lock", "false") == 'true' else False

    if len(mail.title) == 0:
        mail.title = "제목 없는 편지"

    if len(mail.content.strip()) == 0:
        return error("빈 편지는 저장 할 수 없습니다.")

    db.session.add(mail)
    db.session.commit()

    # encrypt after mail created
    try:
        mail.content = encrypt_mail(
            owner_id=user.id,
            mail_id=mail.id,
            content=content
        )
    except (ValueError, Exception) as e:
        logger.exception(e)
        return error(message="메일을 저장하는데 오류가 발생했습니다.")

    db.session.commit()

    return render_template(
        "mail/write/clear-storage.html",
        mail_id='new',
        url=url_for("dashboard.index"),
    )


@bp.get("/edit/<int:mail_id>")
@login_required
@fetch_mail
def edit(user: User, mail: Mail, mail_id: int):
    g.editor_css = True

    try:
        mail.content = decrypt_mail(
            owner_id=user.id,
            mail_id=mail_id,
            result=mail.content
        )
    except (ValueError, Exception) as e:
        logger.exception(e)
        error_id = set_error_message(message="메일을 불러오는데 오류가 발생했습니다.")
        return redirect(url_for("dashboard.index", error=error_id))

    return render_template(
        "mail/write/edit.html",
        m=mail,
        error=get_error_message(),
        csrf=create_csrf_token()
    )


@bp.post("/edit/<int:mail_id>")
@login_required
@fetch_mail
@check_user_lock
def edit_post(user: User, mail: Mail, mail_id: int):
    try:
        csrf = request.form['csrf']
        if not verify_csrf_token(csrf_token=csrf):
            return redirect(url_for("mail.write.edit",
                                    mail_id=mail_id,
                                    error=set_error_message(["CSRF 토큰이 올바르지 않습니다."])))
    except KeyError:
        return redirect(url_for("mail.write.edit",
                                mail_id=mail_id,
                                error=set_error_message(["CSRF 토큰이 없습니다."])))

    error = []

    try:
        title = request.form['title'].strip()
        if len(title) > 100:
            error.append("제목이 100자 보다 길 수 없습니다.")
        else:
            if len(title) == 0:
                title = "제목 없는 편지"

            mail.title = title
    except KeyError:
        error.append("제목을 전달 받지 못 했습니다.")

    try:
        content = request.form['content']
        if len(content) > 20000:
            error.append("본문이 20000자 보다 길 수 없습니다.")
        else:
            if len(content.strip()) == 0:
                error.append("빈 편지는 저장 할 수 없습니다.")
            else:
                mail.content = content
    except KeyError:
        error.append("편지 본문을 전달 받지 못 했습니다.")

    try:
        # 편지를 보낼 날짜를 불러옴
        send_date = datetime.strptime(request.form['date'], "%Y-%m-%d")

        # 하루 200통 체크
        if check_date_limit(date=send_date):
            error.append(f"해당 날짜에 보내는 편지가 <b>{SEND_LIMIT}</b>통이 넘어 해당 날짜를 선택 할 수 없습니다.")
            raise ValueError("skip this request!")

        # 같은 요일에 보내는 편지를 작성한 적이 있다면 거부
        test = Mail.query.filter_by(
            owner_id=mail.owner_id,
            send_date=send_date
        ).filter(
            Mail.id != mail.id
        ).first()

        if test is not None:
            date = send_date.strftime("%Y년 %m월 %d일")
            error.append(f"<b>{date}</b>로 보내는 편지가 이미 있습니다.")
            raise ValueError("skip this request!")

        # 기준 날짜 = 편지 생성 날짜
        days = (send_date - mail.creation_date).days + 1

        if days < MIN_DAYS:
            # 보낼 날짜가 너무 가까움
            error.append("발송일은 최소 7일후로 설정 할 수 있습니다.")
        elif days > MAX_DAYS:
            # 보낼 날짜가 너무 멈
            error.append("발송일은 최대 작성일로 부터 13개월까지 설정 할 수 있습니다.")
        else:
            mail.send_date = send_date
    except (KeyError, ValueError):
        # 값을 변경 하지 않음
        pass

    mail.lock = True if request.form.get("lock", "false") == 'true' else False

    try:
        mail.content = encrypt_mail(
            owner_id=user.id,
            mail_id=mail_id,
            content=mail.content
        )
    except (ValueError, Exception) as e:
        logger.exception(e)
        error_id = set_error_message(message=["메일을 저장하는데 문제가 발생했습니다."])
        return redirect(url_for("mail.write.edit", mail_id=mail_id, error=error_id))

    db.session.commit()

    if len(error) != 0:
        error_id = set_error_message(message=error)
        return redirect(url_for("mail.write.edit", mail_id=mail_id, error=error_id))

    return render_template(
        "mail/write/clear-storage.html",
        mail_id=mail_id,
        url=url_for("dashboard.index"),
    )


@bp.get("/delete/<int:mail_id>")
@login_required
@check_user_lock
def delete(user: User, mail_id: int):
    def resp(key: str, message: str):
        kwargs = {key: set_error_message(message=message)}
        return redirect(url_for("dashboard.index", **kwargs))

    mail = Mail.query.filter_by(
        id=mail_id,
        owner_id=user.id,
        lock=False
    ).delete()

    if mail == 0:
        return resp(
            key="error",
            message="삭제할 편지를 찾지 못 했습니다."
        )

    db.session.commit()

    delete_key_store(
        owner_id=user.id,
        mail_id=mail_id
    )

    return resp(
        key="message",
        message="해당 편지를 삭제했습니다."
    )
