from os import environ
from datetime import datetime

from flask import Blueprint
from flask import session
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template
from sqlalchemy.exc import IntegrityError

from app import db
from app.utils import get_ip
from app.utils import get_error_message
from app.utils import set_error_message
from app.utils import login_block
from app.models import User
from app.models import LoginHistory
from app.models import Code
from app.models import TermsOfService
from app.models import PrivacyPolicy
from kakao.utils import verify_step

bp = Blueprint("sign_up", __name__, url_prefix="/sign-up")


def to(message: str):
    error_id = set_error_message(message=message)
    return redirect(url_for("auth.error", error=error_id))


@bp.get("/step1")
@login_block
@verify_step(1)
def step1():
    email = session['social.kakao.email']
    code_id = session['social.kakao.code_id']

    code: Code = Code.query.filter_by(
        id=code_id,
        email=email
    ).first()

    if code is None:
        return to(message="만료된 이메일 인증 요청입니다. 다시 시도해주세요.")

    if code.is_expired() or code.is_used():
        return to(message="만료된 이메일 인증 요청입니다. 다시 시도해주세요.")

    return render_template(
        "kakao/sign-up/step1.html",
        error=get_error_message(),
        email=environ['SMTP_USER']
    )


@bp.post("/step1")
@verify_step(1)
def step1_post():
    email = session['social.kakao.email']
    code_id = session['social.kakao.code_id']

    code: Code = Code.query.filter_by(
        id=code_id,
        email=email
    ).first()

    if code is None:
        return to(message="만료된 이메일 인증 요청입니다. 다시 시도해주세요.")

    if code.is_expired() or code.is_used():
        return to(message="만료된 이메일 인증 요청입니다. 다시 시도해주세요.")

    if code.code == request.form.get("code", "undefined"):
        session['social.kakao.step'] = 2
        # used in step1
        del session['social.kakao.code_id']
        return redirect(url_for("social.kakao.sign_up.step2"))

    error_id = set_error_message(message="인증 코드가 올바르지 않습니다.")
    return redirect(url_for("social.kakao.sign_up.step1", error=error_id))


@bp.get("/step2")
@login_block
@verify_step(2)
def step2():
    try:
        email = session['social.kakao.email']
    except KeyError:
        return to(message="올바른 요청이 아닙니다")

    tos = TermsOfService.query.order_by(
        TermsOfService.id.desc()
    ).with_entities(
        TermsOfService.id
    ).first()

    privacy = PrivacyPolicy.query.order_by(
        PrivacyPolicy.id.desc()
    ).with_entities(
        PrivacyPolicy.id
    ).first()

    if tos is None or privacy is None:
        return "서비스 이용약관과 개인정보 처리방침이 등록되지 않아 회원가입을 진행 할 수 없습니다."

    session['social.kakao.version'] = {
        "tos": tos.id,
        "privacy": privacy.id
    }

    return render_template(
        "kakao/sign-up/step2.html",
        error=get_error_message()
    )


@bp.post("/step2")
@login_block
@verify_step(2)
def step2_post():
    def _to(message: str):
        error_id = set_error_message(message=message)
        return redirect(url_for("social.kakao.sign_up.step2", error=error_id))

    tos_agree = request.form.get("tos_agree", None) == "on"
    privacy_agree = request.form.get("privacy_agree", None) == "on"

    if tos_agree is False:
        return _to(message="서비스 이용약관에 동의해야 서비스를 이용 할 수 있습니다.")

    if privacy_agree is False:
        return _to(message="개인정보 처리방침에 동의해야 서비스를 이용 할 수 있습니다.")

    try:
        id = session['social.kakao.id']
        email = session['social.kakao.email']
        version = session['social.kakao.version']
    except KeyError:
        return to(message="올바른 요청이 아닙니다")

    user = User()
    user.email = email
    user.oauth = "kakao"
    user.oauth_id = id
    user.admin = False

    user.tos = version['tos']
    user.privacy = version['privacy']

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        user = User.query.filter_by(
            email=email
        ).first()

        if user is None:
            return _to(message="회원가입에 실패했습니다. "
                               "동일한 문제가 반복해서 발생하는 경우 관리자한테 문의해주세요.")

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

    del session['social.kakao.id']
    del session['social.kakao.email']
    del session['social.kakao.step']
    # used in step2
    del session['social.kakao.version']

    return redirect(url_for("dashboard.index"))
