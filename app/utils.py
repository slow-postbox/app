from secrets import token_hex
from functools import wraps

from flask import request
from flask import session
from flask import redirect
from flask import url_for

from app.models import User
from app.models import LoginHistory
from app.models import Mail


def get_ip() -> str:
    return request.headers.get("X-Forwarded-For", request.remote_addr)


def get_error_message() -> str or list or None:
    error_id = request.args.get("error", None)
    if error_id not in session:
        return None

    error_message = session[error_id]
    del session[error_id]
    return error_message


def set_error_message(message: str or list):
    error_id = token_hex(16)
    session[error_id] = message
    return error_id


def login_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        try:
            user_id = session['user']['user_id']
        except KeyError:
            error_id = set_error_message(message="로그인이 필요합니다.")
            return redirect(url_for("auth.login", error=error_id))

        user = User.query.filter_by(
            id=user_id
        ).first()

        if user is None:
            del session['user']
            error_id = set_error_message(message="삭제된 계정입니다.")
            return redirect(url_for("auth.sign_up", error=error_id))

        history = LoginHistory.query.with_entities(
            LoginHistory.id
        ).filter_by(
            id=session['user']['history_id'],
            owner_id=user_id,
        ).first()

        if history is None:
            del session['user']
            error_id = set_error_message(message="로그인 기록이 없는 세션입니다.")
            return redirect(url_for("auth.login", error=error_id))

        kwargs.update({"user": user})
        return f(*args, **kwargs)

    return decorator


def login_block(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if 'user' in session:
            return redirect(url_for("dashboard.index"))

        return f(*args, **kwargs)

    return decorator


def fetch_mail(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        user = kwargs.get("user", None)
        mail_id = kwargs.get("mail_id", None)

        if user is not None and mail_id is not None:
            mail = Mail.query.filter_by(
                id=mail_id,
                owner_id=user.id
            ).first()
        else:
            mail = None

        kwargs.update({"mail": mail})
        return f(*args, **kwargs)

    return decorator
