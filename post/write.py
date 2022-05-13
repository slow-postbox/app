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

bp = Blueprint("write", __name__, url_prefix="/write")


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
    mail = Mail()
    mail.owner_id = user.id
    mail.send_date = datetime.strptime(request.form['date'], "%Y-%m-%d")
    mail.title = request.form['title']
    mail.content = request.form['content']
    mail.lock = False

    db.session.add(mail)
    db.session.commit()

    return redirect(url_for("mail.edit", mail_id=mail.id))


@bp.get("/<int:mail_id>")
@login_required
@fetch_mail
def edit(user: User, mail: Mail, mail_id: int):
    g.editor_css = True
    return render_template(
        "post/write/edit.html",
    )


@bp.post("/<int:mail_id>")
@login_required
@fetch_mail
def edit_post(user: User, mail: Mail, mail_id: int):
    print(mail_id, user, mail)
    return "WIP : check console"
