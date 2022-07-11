from os import environ
from typing import Tuple
from functools import wraps

from flask import session
from flask import url_for
from flask import redirect
from requests import post


class KakaoLoginFail(Exception):
    def __init__(self):
        super().__init__()


class KakaoAuthFail(Exception):
    def __init__(self):
        super().__init__()


class KakaoAgreementRequired(Exception):
    def __init__(self):
        super().__init__()


class KakaoEmailVerifyRequired(Exception):
    def __init__(self, id, email):
        self.id = id
        self.email = email
        super().__init__()


def code_to_token(code: str) -> str:
    resp = post(
        url="https://kauth.kakao.com/oauth/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
        },
        data={
            "grant_type": "authorization_code",
            "client_id": environ['KAKAO_REST_API_KEY'],
            "redirect_uri": environ['HOST'] + url_for("social.kakao.callback.index"),
            "code": code
        }
    )

    if resp.ok:
        json = resp.json()
        return "Bearer " + json['access_token']
    else:
        raise KakaoLoginFail


def get_email_with_token(token: str) -> Tuple[int, str]:
    resp = post(
        url="https://kapi.kakao.com/v2/user/me",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": token,
        },
        data={
            "property_keys": """["kakao_account.email"]"""
        }
    )

    if not resp.ok:
        raise KakaoAuthFail

    json = resp.json()
    kakao_account = json['kakao_account']

    if kakao_account['email_needs_agreement']:
        raise KakaoAgreementRequired

    if kakao_account['is_email_valid'] is True and kakao_account['is_email_verified'] is True:
        return json['id'], kakao_account['email']

    raise KakaoEmailVerifyRequired(
        id=json['id'],
        email=kakao_account['email']
    )


def verify_step(step: int):
    def wrapper(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            step_from_session = session.get("social.kakao.step", None)
            if step_from_session is None:
                return "요청이 올바르지 않습니다. (회원가입 과정 정보가 없음)", 400

            if step == step_from_session:
                return f(*args, **kwargs)
            else:
                return redirect(url_for(f"social.kakao.sign_up.step{step_from_session}"))

        return decorator

    return wrapper
