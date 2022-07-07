from functools import wraps
from urllib import parse
from typing import NamedTuple

from flask import current_app
from flask import redirect
from flask import url_for
from requests import get
from requests import post
from requests import delete

from .send import send_token as _send_token
from app.models import UserLock
from app.utils import set_error_message

send_token = _send_token


class KeyStore(NamedTuple):
    key: str
    iv: str


def get_headers() -> dict:
    return {
        "User-Agent": "chick0/slow_postbox",
        "Authorization": f"Bearer {current_app.config['KEY_STORE']}"
    }


def get_url(owner_id: int, mail_id: int) -> str:
    payload = parse.urlencode(query=dict(
        owner_id=owner_id,
        mail_id=mail_id
    ))

    return f"http://127.0.0.1:15882/v1/key?{payload}"


def fetch_key_store(owner_id: int, mail_id: int) -> KeyStore:
    resp = get(
        url=get_url(
            owner_id=owner_id,
            mail_id=mail_id
        ),
        headers=get_headers()
    )

    if resp.status_code == 404:
        return create_key_store(
            owner_id=owner_id,
            mail_id=mail_id
        )

    json = resp.json()

    return KeyStore(
        key=json['key'],
        iv=json['iv']
    )


def create_key_store(owner_id: int, mail_id: int) -> KeyStore:
    resp = post(
        url=get_url(
            owner_id=owner_id,
            mail_id=mail_id
        ),
        headers=get_headers()
    )

    json = resp.json()

    return KeyStore(
        key=json['key'],
        iv=json['iv']
    )


def delete_key_store(owner_id: int, mail_id: int) -> None:
    delete(
        url=get_url(
            owner_id=owner_id,
            mail_id=mail_id,
        ),
        headers=get_headers()
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
