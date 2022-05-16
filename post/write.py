from datetime import datetime
from datetime import timedelta

from flask import Blueprint
from flask import g
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template

from app import db
from app.models import User
from app.models import Mail
from app.utils import login_required
from app.utils import fetch_mail
from app.utils import get_error_message
from app.utils import set_error_message

bp = Blueprint("write", __name__, url_prefix="/")

# 최소 1주일
MIN_DAYS = 7
# 최대 1년하고 4주일
MAX_DAYS = 365 + timedelta(weeks=4).days
# 편지 개수 제한
MAIL_LIMIT = 20


@bp.get("/create-new")
@login_required
def create_new(user: User):
    if Mail.query.filter_by(
        owner_id=user.id
    ).count() >= MAIL_LIMIT:
        return render_template(
            "post/write/limit.html",
            limit=MAIL_LIMIT
        )

    g.editor_css = True
    return render_template(
        "post/write/create-new.html",
        date=(datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
        error=get_error_message()
    )


@bp.post("/create-new")
@login_required
def create_new_post(user: User):
    if Mail.query.filter_by(
        owner_id=user.id
    ).count() >= MAIL_LIMIT:
        return render_template(
            "post/write/limit.html",
            limit=MAIL_LIMIT
        )

    def error(message):
        error_id = set_error_message(message=message)
        return redirect(url_for("post.write.create_new", error=error_id))

    try:
        content = request.form['content']

        if len(content) > 20000:
            return error("본문이 20000자 보다 길 수 없습니다.")
    except KeyError:
        return error("편지 본문을 전달 받지 못 했습니다.")

    try:
        # 편지를 보낼 날짜를 불러옴
        send_date = datetime.strptime(request.form['date'], "%Y-%m-%d")

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

    return redirect(url_for("post.write.edit", mail_id=mail.id))


@bp.get("/edit/<int:mail_id>")
@login_required
@fetch_mail
def edit(user: User, mail: Mail, mail_id: int):
    if mail.lock is True:
        return render_template(
            "post/write/locked.html",
            m=mail,
            u=user
        )

    g.editor_css = True
    return render_template(
        "post/write/edit.html",
        m=mail,
        error=get_error_message()
    )


@bp.post("/edit/<int:mail_id>")
@login_required
@fetch_mail
def edit_post(user: User, mail: Mail, mail_id: int):
    if mail.lock is True:
        return render_template(
            "post/write/locked.html",
            m=mail,
            u=user
        )

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

    db.session.commit()

    if len(error) != 0:
        error_id = set_error_message(message=error)
        return redirect(url_for("post.write.edit", mail_id=mail_id, error=error_id))

    # without error message
    return redirect(url_for("post.write.edit", mail_id=mail_id))
