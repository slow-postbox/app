from functools import wraps

from flask import request
from flask import session
from flask import redirect
from flask import url_for

from app.models import User
from app.models import Mail


def get_ip() -> str:
    return request.headers.get("X-Forwarded-For", request.remote_addr)


def login_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        try:
            user_id = session['user']['user_id']
        except KeyError:
            return redirect(url_for("auth.login", error="로그인이 필요합니다."))

        user = User.query.filter_by(
            id=user_id
        ).first()

        if user is None:
            return redirect(url_for("auth.sign_up", error="삭제된 계정입니다."))

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
