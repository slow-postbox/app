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

from mail.send import send_mail as _send_mail

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
        logger.info("try to remove used or expired email verify request")
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

    @register_schedule(timedelta(hours=1).seconds)
    def send_mail():
        session = session_factory()
        today = datetime.strptime(datetime.today().strftime("%Y-%m-%d"), "%Y-%m-%d")
        for mail in session.query(Mail).with_entities(
            Mail.id,
            Mail.status,
            Mail.owner_id,
            Mail.title,
        ).filter(
            Mail.send_date <= today
        ).filter_by(
            # 편지가 우체통에 들어갔고
            lock=True,
            # 해당 편지가 전송된 적이 없다면
            status=False
        ).limit(50).all():
            user = session.query(User).with_entities(
                User.email,
            ).filter_by(
                id=mail.owner_id
            ).first()

            try:
                _send_mail(
                    email=user.email,
                    url=environ['HOST'] + f"/mail/read/{mail.id}",
                    title=mail.title
                )

                # 메일은 전송되었음
                mail.status = True
            except Exception as e:
                logger.critical(f"FAIL TO SEND MAIL / mail_id={mail.id}")
                logger.critical(e.__str__())

        session.commit()

    @register_schedule(timedelta(minutes=15).seconds)
    def remove_old_password_reset():
        logger.info("try to remove used or expired password reset request")
        session = session_factory()
        for password_reset in session.query(PasswordReset).filter(
            or_(
                PasswordReset.used_date != None,
                PasswordReset.creation_date < datetime.now() - timedelta(minutes=5)
            )
        ).limit(50).all():
            logger.info(f"remove password reset request id='{password_reset.id} owner_id='{password_reset.owner_id}'")
            session.delete(password_reset)

        session.commit()


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

