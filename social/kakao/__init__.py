from os import environ

__required__ = [
    "KAKAO_REST_API_KEY",
    "KAKAO_JAVASCRIPT_KEY",
]

if sum([x in environ for x in __required__]) == len(__required__):
    __all__ = [
        "callback",
        "convert",
        "sign_up",
    ]
else:
    __all__ = []


from . import *
