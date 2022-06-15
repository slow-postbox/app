from json import loads
from functools import wraps
from urllib import parse
from urllib.request import Request
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError
from logging import getLogger
from collections import namedtuple

from flask import current_app
from flask import redirect
from flask import url_for

from .send import send_token
from .send import send_password_reset
from app.models import UserLock
from app.utils import set_error_message

KeyStore = namedtuple(
    "KeyStore",
    [
        'key',
        'iv'
    ]
)


def request(
        method: str,  # GET or POST
        owner_id: int,
        mail_id: int
) -> dict:
    payload = parse.urlencode(query=dict(
        owner_id=owner_id,
        mail_id=mail_id
    ))

    req = Request(
        url=f"http://127.0.0.1:15882/v1/key?{payload}",
        method=method,
        headers={
            "User-Agent": "chick0/slow_postbox",
            "Authorization": f"Bearer {current_app.config['KEY_STORE']}"
        }
    )

    resp = urlopen(req, timeout=3)
    return loads(s=resp.read())


def fetch_key_store(owner_id: int, mail_id: int) -> KeyStore:
    try:
        context = request(
            method="GET",
            owner_id=owner_id,
            mail_id=mail_id
        )
    except HTTPError as e:
        if e.code == 404:
            # None -> create *NEW*
            return create_key_store(
                owner_id=owner_id,
                mail_id=mail_id
            )

        logger = getLogger()
        logger.critical(
            "*FAIL TO FETCH KEY STORE* / "
            f"user_id={owner_id}, mail_id={mail_id}, detail={e.read().decode()}"
        )

        raise Exception
    except URLError as e:
        logger = getLogger()
        logger.critical(
            "*FAIL TO CONNECT WITH KEY STORE API * / "
            f"{e.reason}"
        )

        raise Exception

    return KeyStore(
        key=context['key'],
        iv=context['iv']
    )


def create_key_store(owner_id: int, mail_id: int) -> KeyStore:
    try:
        context = request(
            method="POST",
            owner_id=owner_id,
            mail_id=mail_id
        )
    except HTTPError as e:
        logger = getLogger()
        logger.critical(
            "*FAIL TO FETCH KEY STORE* / "
            f"user_id={owner_id}, mail_id={mail_id}, detail={e.read().decode()}"
        )

        raise Exception
    except URLError as e:
        logger = getLogger()
        logger.critical(
            "*FAIL TO CONNECT WITH KEY STORE API * / "
            f"{e.reason}"
        )

        raise Exception

    return KeyStore(
        key=context['key'],
        iv=context['iv']
    )


def delete_key_store(owner_id: int, mail_id: int) -> None:
    try:
        request(
            method="DELETE",
            owner_id=owner_id,
            mail_id=mail_id
        )
    except HTTPError as e:
        logger = getLogger()
        logger.critical(
            "*FAIL TO FETCH KEY STORE* / "
            f"user_id={owner_id}, mail_id={mail_id}, detail={e.read().decode()}"
        )
    except URLError as e:
        logger = getLogger()
        logger.critical(
            "*FAIL TO CONNECT WITH KEY STORE API * / "
            f"{e.reason}"
        )


def check_user_lock(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        user = kwargs['user']

        user_lock = UserLock.query.filter_by(
            owner_id=user.id
        ).count()

        if user_lock != 0:
            error_id = set_error_message(message="계정 잠금 요청에 의해 저장된 편지를 수정 및 삭제 할 수 없습니다.")
            return redirect(url_for("dashboard.index", error=error_id))

        return f(*args, **kwargs)

    return decorator
