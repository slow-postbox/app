from secrets import token_bytes
from datetime import timedelta
from functools import wraps

from flask import request
from flask import session
from flask import redirect
from flask import url_for
from flask import render_template

from app import redis
from app.models import User
from app.models import LoginHistory
from app.models import Mail
from app.models import Notice
from app.models import TermsOfService
from app.models import PrivacyPolicy

CSRF_TOKEN_LENGTH = 64
CSRF_KEY_NAME = "slow_post:csrf:{ip}:{user_id}:{path}"


def get_ip() -> str:
    return request.headers.get("X-Forwarded-For", request.remote_addr)


def get_user_id() -> str:
    return session.get("user", {}).get("user_id", "undefined")


def create_csrf_token() -> str:
    csrf_token = token_bytes(int(CSRF_TOKEN_LENGTH / 2)).hex()
    redis.set(
        name=CSRF_KEY_NAME.format(
            ip=get_ip(),
            user_id=get_user_id(),
            path=request.path
        ),
        value=csrf_token,
        ex=timedelta(hours=1).seconds
    )

    return csrf_token


def verify_csrf_token(csrf_token: str) -> bool:
    if len(csrf_token) != CSRF_TOKEN_LENGTH:
        return False

    name = CSRF_KEY_NAME.format(
        ip=get_ip(),
        user_id=get_user_id(),
        path=request.path
    )

    token = redis.get(name=name)
    if token is None:
        return False

    # remove used csrf token
    redis.delete(name)

    return csrf_token == token.decode()


def get_error_message(argument_key: str = "error") -> str or list or None:
    error_id = request.args.get(argument_key, None)
    if error_id not in session:
        return None

    error_message = session[error_id]
    del session[error_id]
    return error_message


def set_error_message(message: str or list):
    error_id = token_bytes(8).hex()
    session[error_id] = message
    return error_id


def login_after(endpoint):
    def wrapper(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            session['login_after'] = endpoint
            return f(*args, **kwargs)

        return decorator

    return wrapper


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

        session['admin'] = user.admin

        kwargs.update({"user": user})
        return f(*args, **kwargs)

    return decorator


def admin_only(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        user = kwargs.get("user")
        if not user.admin:
            return "권한이 부족합니다."

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

        if mail is None:
            error_id = set_error_message(message="해당 편지를 찾을 수 없습니다.")
            return redirect(url_for("dashboard.index", error=error_id))

        if mail.lock is True:
            return render_template(
                "mail/write/locked.html",
                m=mail,
                u=user
            )

        kwargs.update({"mail": mail})
        return f(*args, **kwargs)

    return decorator


def fetch_notice(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        notice_id = kwargs.get("notice_id")

        notice = Notice.query.filter_by(
            id=notice_id
        ).first()

        if notice is None:
            error_id = set_error_message(message="해당 공지를 찾을 수 없습니다.")
            return redirect(url_for("notice.show_all", error=error_id))

        kwargs.update({"notice": notice})
        return f(*args, **kwargs)

    return decorator


def fetch_tos(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        tos_id = kwargs.get("tos_id")

        tos = TermsOfService.query.filter_by(
            id=tos_id
        ).first()

        if tos is None:
            error_id = set_error_message(message="올바른 서비스 이용약관 버전이 아닙니다.")
            return redirect(url_for("tos.latest", error=error_id))

        kwargs.update({"tos": tos})
        return f(*args, **kwargs)

    return decorator


def fetch_privacy(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        privacy_id = kwargs.get("privacy_id")

        privacy = PrivacyPolicy.query.filter_by(
            id=privacy_id
        ).first()

        if privacy is None:
            error_id = set_error_message(message="올바른 개인정보 처리방침 버전이 아닙니다.")
            return redirect(url_for("privacy.latest", error=error_id))

        kwargs.update({"privacy": privacy})
        return f(*args, **kwargs)

    return decorator
