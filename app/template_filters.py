from os import environ as _environ


def get_env(key: str) -> str:
    return _environ[key]
