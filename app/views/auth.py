from os import environ
from re import compile
from random import choices
from hashlib import sha512
from datetime import datetime

from flask import Blueprint
from flask import session
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template

from app import db
from app.models import User
from app.models import LoginHistory
from app.models import Code
from app.utils import get_ip
from mail import send_token

bp = Blueprint("auth", __name__, url_prefix="/auth")
re = compile(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')


@bp.get("/login")
def login():
    return render_template(
        "auth/login.html",
        error=request.args.get("error", None),
        message=request.args.get("message", None),
    )


@bp.post("/login")
def login_post():
    def error(message: str):
        return redirect(url_for("auth.login", error=message))

    try:
        email = request.form['email'].strip()

        if re.match(email) is None:
            return error("이메일 형식이 올바르지 않습니다.")
    except KeyError:
        return error("이메일을 입력해주세요.")

    try:
        password = request.form['password'].strip()
        if len(password) == 0:
            raise KeyError
    except KeyError:
        return error("비밀번호를 입력해주세요.")

    user = User.query.filter_by(
        email=email,
        password=sha512(password.encode()).hexdigest()
    ).first()

    if user is None:
        return error("이메일 또는 비밀번호가 올바르지 않습니다.")

    # update last login
    user.last_login = datetime.now()
    # create login history
    history = LoginHistory()
    history.owner_id = user.id
    history.ip = get_ip()

    db.session.add(history)
    db.session.commit()

    session['user'] = {
        'user_id': user.id,
        'history_id': history.id,
    }

    return redirect(url_for("dashboard.index"))


@bp.get("/sign-up")
def sign_up():
    if 'sign-up' in session:
        return redirect(url_for("auth.ready"))

    return render_template(
        "auth/sign-up.html",
        error=request.args.get("error", None)
    )


@bp.post("/sign-up")
def sign_up_post():
    def error(message: str):
        return redirect(url_for("auth.sign_up", error=message))

    if 'sign-up' in session:
        return redirect(url_for("auth.ready"))

    try:
        email = request.form['email'].strip()

        if re.match(email) is None:
            return error("이메일 형식이 올바르지 않습니다.")

        if len(email) > 96:
            return error("해당 이메일 주소는 사용 할 수 없습니다.")
    except KeyError:
        return error("이메일을 입력해주세요.")

    try:
        password = request.form['password'].strip()
    except KeyError:
        return error("비밀번호를 입력해주세요.")

    if len(password) <= 8:
        return error("비밀번호가 너무 짧습니다.")

    user = User.query.filter_by(
        email=email
    ).first()

    if user is not None:
        return error("이미 가입된 계정입니다.")

    _ = [x for x in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"]
    code = Code()
    code.code = "".join(choices(_, k=4) + ['-'] + choices(_, k=4))
    code.ip = get_ip()

    db.session.add(code)
    db.session.commit()

    send_token(
        email=email,
        code=code.code,
        ip=code.ip
    )

    session['sign-up'] = {
        "email": email,
        "password": sha512(password.encode()).hexdigest(),
        "code_id": code.id,
    }

    return redirect(url_for("auth.ready"))


@bp.get("/ready")
def ready():
    if 'sign-up' not in session:
        return redirect(url_for("auth.sign_up"))

    return render_template(
        "auth/ready.html",
        error=request.args.get("error", None),
        email=environ['SMTP_USER'],
    )


@bp.post("/ready")
def ready_post():
    if 'sign-up' not in session:
        return redirect(url_for("auth.sign_up"))

    try:
        code = Code.query.filter_by(
            id=session['sign-up']['code_id'],
            code=request.form['code'].strip()[:9],
            used_date=None
        ).first()

        if code is None:
            return redirect(url_for("auth.ready", error="인증 코드가 올바르지 않습니다."))
    except KeyError:
        return redirect(url_for("auth.ready", error="인증 코드를 입력해주세요."))

    if code.is_expired():
        del session['sign-up']
        return redirect(url_for("auth.sign_up", error="해당 인증 코드는 만료된 코드 입니다."))

    if code.is_used():
        del session['sign-up']
        return redirect(url_for("auth.sign_up", error="해당 인증 코드는 이미 사용된 코드입니다."))

    code.used_date = datetime.now()
    db.session.commit()

    user = User()
    user.email = session['sign-up']['email']
    user.password = session['sign-up']['password']

    db.session.add(user)
    db.session.commit()

    del session['sign-up']
    return redirect(url_for("auth.login", message="방금 가입한 계정으로 다시 로그인 해주세요."))


@bp.get("/password-reset")
def password_reset():
    return render_template(
        "auth/password-reset.html"
    )


@bp.post("/password-reset")
def password_reset_post():
    return
