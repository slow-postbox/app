from os import environ
from time import time
from time import sleep
from sched import scheduler
from functools import wraps
from datetime import datetime
from datetime import timedelta
from logging import INFO
from logging import getLogger
from logging import StreamHandler
from logging import Formatter

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import or_
from sqlalchemy.orm import sessionmaker

from app.models import User
from app.models import LoginHistory
from app.models import Code
from app.models import Mail
from app.models import PasswordReset

logger = getLogger()
s = scheduler(time, sleep)
schedule = {}


def register_schedule(delay: int):
    def wrapper(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            s.enter(**schedule[f.__name__])
            return f(*args, **kwargs)

        schedule.update({
            f.__name__: {
                "delay": delay,
                "priority": 1,
                "action": decorator
            }
        })

        decorator()
        return decorator
    return wrapper


def main():
    # TODO:유저 삭제
    def remove_old_user():
        return

    @register_schedule(timedelta(minutes=30).seconds)
    def remove_old_login_history():
        logger.info("try to remove old login history")
        session = session_factory()
        for history in session.query(LoginHistory).filter(
            LoginHistory.creation_date < datetime.now() - timedelta(days=30)
        ).limit(50).all():
            session.delete(history)
            session.commit()

    @register_schedule(timedelta(minutes=10).seconds)
    def remove_used_or_expired_email_request():
        logger.info("try to used or expired email verify request")
        session = session_factory()
        for code in session.query(Code).filter(
            or_(
                Code.used_date != None,
                Code.creation_date < datetime.now() - timedelta(minutes=3)
            )
        ).limit(50).all():
            logger.info(f"remove email verify code target_email='{code.email}'")
            session.delete(code)
            session.commit()

    # TODO:시간된 메일 전송
    def send_mail():
        return

    # TODO:오래된 비밀번호 재설정 기록 삭제
    def remove_old_password_reset():
        return


if __name__ == "__main__":
    load_dotenv()
    logger.setLevel(INFO)
    handler = StreamHandler()
    handler.setFormatter(fmt=Formatter("%(asctime)s [%(levelname)s]: %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(hdlr=handler)

    engine = create_engine(environ.get("SQLALCHEMY_DATABASE_URI"))
    session_factory = sessionmaker(bind=engine)

    main()

    try:
        s.run()
    except KeyboardInterrupt:
        logger.info("exited!")

