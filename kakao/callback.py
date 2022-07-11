from datetime import datetime

from flask import Blueprint
from flask import session
from flask import request
from flask import redirect
from flask import url_for

from app import db
from app.utils import get_ip
from app.utils import set_error_message
from app.utils import test_email_with_dns
from app.utils import login_block
from app.models import User
from app.models import LoginHistory
from kakao.utils import code_to_token
from kakao.utils import get_email_with_token
from kakao.utils import KakaoLoginFail
from kakao.utils import KakaoAuthFail
from kakao.utils import KakaoAgreementRequired
from kakao.utils import KakaoEmailVerifyRequired

bp = Blueprint("callback", __name__, url_prefix="/callback")


def to(message: str):
    error_id = set_error_message(message=message)
    return redirect(url_for("auth.error", error_social=error_id))


@bp.get("")
@login_block
def index():
    code = request.args.get("code", "undefined")
    if code == "undefined":
        return to(message="잘못된 요청이 입니다.")

    try:
        token = code_to_token(
            code=code
        )
    except KakaoLoginFail:
        return to(message="코드가 올바르지 않습니다.")

    try:
        id, email = get_email_with_token(
            token=token
        )
    except KakaoAuthFail:
        return to(message="카카오 로그인 요청이 올바르지 않습니다.")
    except KakaoAgreementRequired:
        return "오류 / 이메일 동의하지 않음"
    except KakaoEmailVerifyRequired as e:
        return f"오류 / 이메일 인증이 필요함 / {e.email}"

    result = test_email_with_dns(email=email)
    if len(result) != 0:
        return to(message=result)

    # search user
    user: User = User.query.filter_by(
        oauth_id=id,
    ).first()

    if user is None:
        session['social.kakao.id'] = id
        session['social.kakao.email'] = email
        session['social.kakao.step'] = 2
        return redirect(url_for("social.kakao.sign_up.step2"))

    if user.oauth != "kakao":
        return to(message="카카오 계정으로 가입된 계정이 아닙니다.")

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
