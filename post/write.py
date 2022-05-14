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

bp = Blueprint("write", __name__, url_prefix="/")


@bp.get("/create-new")
@login_required
def create_new(user: User):
    g.editor_css = True
    return render_template(
        "post/write/create-new.html",
        date=(datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    )


@bp.post("/create-new")
@login_required
def create_new_post(user: User):
    def error(message):
        return redirect(url_for("post.write.create_new", error=message))

    try:
        content = request.form['content']

        if len(content) > 20000:
            return error("본문이 20000자 보다 길 수 없습니다.")
    except KeyError:
        return error("편지 본문을 전달 받지 못 했습니다.")

    try:
        # 편지를 보낼 날짜를 불러옴
        send_date = datetime.strptime(request.form['date'], "%Y-%m-%d")
    except KeyError:
        # 기본 값은 작성일로부터 1년뒤
        send_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")

    print(
        send_date - datetime.now(),
        send_date - datetime.now() > timedelta(days=365 + 15),
        send_date > datetime.now(),
        send_date < datetime.now(),
    )

    mail = Mail()
    mail.owner_id = user.id
    mail.send_date = send_date
    mail.title = request.form.get("title", "제목 없는 편지").strip()[:100]
    mail.content = content
    mail.lock = True if request.form.get("lock", "false") == 'true' else False

    db.session.add(mail)
    db.session.commit()

    return redirect(url_for("post.write.edit", mail_id=mail.id))


@bp.get("/edit/<int:mail_id>")
@login_required
@fetch_mail
def edit(user: User, mail: Mail, mail_id: int):
    if mail.lock is True:
        return "해당 편지는 수정할 수 없습니다."

    g.editor_css = True
    return render_template(
        "post/write/edit.html",
        m=mail
    )


@bp.post("/edit/<int:mail_id>")
@login_required
@fetch_mail
def edit_post(user: User, mail: Mail, mail_id: int):
    if mail.lock is True:
        return "해당 편지는 수정할 수 없습니다."

    print(mail_id, user, mail)
    return "WIP : check console"
