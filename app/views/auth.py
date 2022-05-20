from os import environ
from re import compile
from random import choices
from hashlib import sha512
from datetime import datetime
from datetime import timedelta

from flask import Blueprint
from flask import session
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import User
from app.models import LoginHistory
from app.models import Code
from app.models import TermsOfService
from app.models import PrivacyPolicy
from app.utils import get_ip
from app.utils import login_block
from app.utils import get_error_message
from app.utils import set_error_message
from mail.utils import send_token

bp = Blueprint("auth", __name__, url_prefix="/auth")
re = compile(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')

alert = "\n".join([
    "<p>- <b>{name}</b>이 업데이트 되었습니다.</p>",
    "<p>- 변경된 <b>{name}</b>은 <b>{date}</b>부터 시행됩니다.</p>",
])


@bp.get("/logout")
def logout():
    for key in list(session.keys()):
        del session[key]

    return redirect(url_for("auth.login", message="logout"))


@bp.get("/login")
@login_block
def login():
    message = {
        "logout": "로그아웃 되었습니다.",
        "sign-up": "방금 가입한 계정으로 다시 로그인 해주세요."
    }.get(request.args.get("message"), None)

    return render_template(
        "auth/login.html",
        error=get_error_message(),
        message=message,
    )


@bp.post("/login")
@login_block
def login_post():
    def error(message: str):
        error_id = set_error_message(message=message)
        return redirect(url_for("auth.login", error=error_id))

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

    alerts = []

    # get latest tos version
    tos = TermsOfService.query.order_by(
        TermsOfService.id.desc()
    ).with_entities(
        TermsOfService.id,
        TermsOfService.creation_date,
    ).first()

    # get latest privacy police version
    privacy = PrivacyPolicy.query.order_by(
        PrivacyPolicy.id.desc()
    ).with_entities(
        PrivacyPolicy.id,
        PrivacyPolicy.creation_date,
    ).first()

    if tos.id != user.tos:
        user.tos = tos.id
        alerts.append(alert.format(
            name="서비스 이용약관",
            date=(tos.creation_date + timedelta(days=7)).strftime("%Y년 %m월 %d일"),
        ))

    if privacy.id != user.privacy:
        user.privacy = privacy.id
        alerts.append(alert.format(
            name="개인정보 처리방침",
            date=(privacy.creation_date + timedelta(days=7)).strftime("%Y년 %m월 %d일"),
        ))

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

    if len(alerts) == 0:
        try:
            endpoint = session['login_after']
            del session['login_after']
        except KeyError:
            endpoint = "dashboard.index"

        return redirect(url_for(endpoint))
    else:
        message_id = set_error_message("<br>".join(alerts))
        return redirect(url_for("dashboard.index", message=message_id))


@bp.get("/sign-up")
@login_block
def sign_up():
    if 'sign-up' in session:
        return redirect(url_for("auth.ready"))

    tos = TermsOfService.query.order_by(
        TermsOfService.id.desc()
    ).first()

    privacy = PrivacyPolicy.query.order_by(
        PrivacyPolicy.id.desc()
    ).first()

    if tos is None or privacy is None:
        return "서비스 이용약관과 개인정보 처리방침이 등록되지 않아 회원가입을 진행 할 수 없습니다."

    session['sign-up-version'] = {
        "tos": tos.id,
        "privacy": privacy.id
    }

    return render_template(
        "auth/sign-up.html",
        error=get_error_message(),
        tos=tos,
        privacy=privacy,
    )


@bp.post("/sign-up")
@login_block
def sign_up_post():
    def error(message: str):
        error_id = set_error_message(message=message)
        return redirect(url_for("auth.sign_up", error=error_id))

    if 'sign-up' in session:
        return redirect(url_for("auth.ready"))

    tos_agree = request.form.get("tos_agree", None) == "on"
    privacy_agree = request.form.get("privacy_agree", None) == "on"

    if tos_agree is False:
        return error("서비스 이용약관에 동의해야 서비스를 이용 할 수 있습니다.")

    if privacy_agree is False:
        return error("개인정보 처리방침에 동의해야 서비스를 이용 할 수 있습니다.")

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

    if Code.query.with_entities(Code.id).filter_by(
        email=email,
        used_date=None
    ).filter(
        # 만료되지 않은 코드
        Code.creation_date >= datetime.now() - timedelta(minutes=3)
    ).first() is not None:
        return error("다른 세션에서 회원가입이 진행중인 이메일 계정 입니다.")

    _ = [x for x in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"]
    code = Code()
    code.email = email
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
@login_block
def ready():
    if 'sign-up' not in session:
        return redirect(url_for("auth.sign_up"))

    return render_template(
        "auth/ready.html",
        error=get_error_message(),
        email=environ['SMTP_USER'],
    )


@bp.post("/ready")
@login_block
def ready_post():
    def error(message: str, endpoint: str = "auth.ready"):
        error_id = set_error_message(message=message)
        return redirect(url_for(endpoint, error=error_id))

    if 'sign-up' not in session:
        return redirect(url_for("auth.sign_up"))

    try:
        code = Code.query.filter_by(
            id=session['sign-up']['code_id'],
            code=request.form['code'].strip()[:9],
            used_date=None
        ).first()

        if code is None:
            return error("인증 코드가 올바르지 않습니다.")
    except KeyError:
        return error("인증 코드를 입력해주세요.")

    if code.is_expired():
        del session['sign-up']
        return error("해당 인증 코드는 만료된 코드 입니다.", "auth.sign_up")

    if code.is_used():
        del session['sign-up']
        return error("해당 인증 코드는 이미 사용된 코드입니다.", "auth.sign_up")

    code.used_date = datetime.now()
    db.session.commit()

    user = User()
    user.email = session['sign-up']['email']
    user.password = session['sign-up']['password']
    user.admin = False

    user.tos = session['sign-up-version']['tos']
    user.privacy = session['sign-up-version']['privacy']
    del session['sign-up-version']

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        del session['sign-up']
        return error("해당 이메일 주소는 다른 세션에서 회원가입이 완료되었습니다.", "auth.login")

    del session['sign-up']
    return redirect(url_for("auth.login", message="sign-up"))


@bp.get("/password-reset")
@login_block
def password_reset():
    return render_template(
        "auth/password-reset.html"
    )


@bp.post("/password-reset")
@login_block
def password_reset_post():
    return
