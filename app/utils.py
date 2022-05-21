from secrets import token_bytes
from datetime import timedelta
from functools import wraps

from flask import request
from flask import session
from flask import redirect
from flask import url_for

from app import redis
from app.models import User
from app.models import LoginHistory
from app.models import Mail
from app.models import Notice
from app.models import TermsOfService
from app.models import PrivacyPolicy


def get_ip() -> str:
    return request.headers.get("X-Forwarded-For", request.remote_addr)


def create_csrf_token() -> str:
    session_id = token_bytes(int(32 / 2)).hex()
    csrf_token = token_bytes(int(64 / 2)).hex()
    ip = get_ip()

    redis.set(
        name=f"slow_postbox:csrf:{ip}:{session_id}",
        value=csrf_token,
        ex=timedelta(hours=1).seconds
    )

    return session_id + csrf_token


def verify_csrf_token(csrf_token: str) -> bool:
    if len(csrf_token) != (32 + 64):
        return False

    session_id = csrf_token[:32]
    csrf_token = csrf_token[32:]
    ip = get_ip()

    token = redis.get(name=f"slow_postbox:csrf:{ip}:{session_id}")
    if token is None:
        return False

    # remove used csrf token
    redis.delete(f"slow_postbox:csrf:{ip}:{session_id}")

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
