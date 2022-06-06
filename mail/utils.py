from json import loads
from urllib import parse
from urllib.request import Request
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError
from logging import getLogger
from collections import namedtuple

from flask import current_app

from .send import send_token
from .send import send_password_reset


KeyStore = namedtuple(
    "KeyStore",
    [
        'key',
        'iv'
    ]
)


def fetch_key_store(owner_id: int, mail_id: int) -> KeyStore or None:
    def fetch_from_api():
        payload = parse.urlencode(query=dict(
            owner_id=owner_id,
            mail_id=mail_id
        ))

        req = Request(
            url="http://127.0.0.1:15882/v1/key?" + payload,
            method="GET",
            headers={
                "User-Agent": "chick0/slow_postbox",
                "Authorization": f"Bearer {current_app.config['KEY_STORE']}"
            }
        )

        resp = urlopen(req, timeout=3)
        return loads(s=resp.read())

    try:
        context = fetch_from_api()
    except HTTPError as e:
        logger = getLogger()
        logger.critical(
            "*FAIL TO FETCH KEY STORE* / "
            f"user_id={owner_id}, mail_id={mail_id}, detail={e.read().decode()}"
        )

        return None
    except URLError as e:
        logger = getLogger()
        logger.critical(
            "*FAIL TO CONNECT WITH KEY STORE API * / "
            f"{e.reason}"
        )

        return None

    return KeyStore(
        key=context['key'],
        iv=context['iv']
    )
