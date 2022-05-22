from hashlib import sha512
from datetime import datetime
from datetime import timedelta
from functools import wraps

from flask import Blueprint
from flask import request
from flask import redirect
from flask import url_for
from flask import render_template

from app import db
from app.models import User
from app.models import PasswordReset
from app.utils import login_block
from app.utils import get_ip
from app.utils import get_error_message
from app.utils import set_error_message

bp = Blueprint("reset", __name__, url_prefix="/reset")


def fetch_reset(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        user_id = kwargs['user_id']
        token = kwargs['token']

        pw = PasswordReset.query.filter_by(
            owner_id=user_id,
            token=token,
            used_date=None
        ).first()

        if pw is None:
            return render_template(
                "reset/none.html"
            )

        # 사용 여부 검증은 DB 퀴리로 진행

        if pw.is_expired():
            return render_template(
                "reset/expired.html"
            )

        kwargs.update({'pw': pw})
        return f(*args, **kwargs)

    return decorator


@bp.get("/<int:user_id>/<string:token>")
@login_block
@fetch_reset
def password_input(pw: PasswordReset, user_id: int, token: str):
    return render_template(
        "reset/password-input.html",
        error=get_error_message(),
        expired=(pw.creation_date + timedelta(minutes=5)).strftime("%H시 %M분")
    )


@bp.post("/<int:user_id>/<string:token>")
@login_block
@fetch_reset
def password_input_post(pw: PasswordReset, user_id: int, token: str):
    def error(message: str):
        error_id = set_error_message(message=message)
        return redirect(url_for("reset.password_input", user_id=user_id, token=token, error=error_id))

    try:
        password = request.form['password'].strip()
    except KeyError:
        return error("비밀번호를 입력해주세요.")

    if len(password) <= 8:
        return error("비밀번호가 너무 짧습니다.")

    user = User.query.filter_by(
        id=user_id
    ).first()

    if user is None:
        return "대상 계정을 찾을 수 없습니다."

    # update password
    user.password = sha512(password.encode()).hexdigest()
    # update password reset request
    pw.use_ip = get_ip()
    pw.used_date = datetime.now()
    db.session.commit()

    return redirect(url_for("auth.login", message="reset"))
