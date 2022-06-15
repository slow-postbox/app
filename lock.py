from os import environ

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from app.models import User
from app.models import UserLock

engine = None


def init_engine():
    load_dotenv()
    globals().update({
        "engine": create_engine(environ.get("SQLALCHEMY_DATABASE_URI"))
    })


def select_user(session) -> User:
    print("\n* select user to clear user lock *\n")
    user = session.query(User).filter_by(
        email=input("(string) user_email : ")
    ).first()

    print("\n* selected user is", user.id, user.email)
    return user


def main():
    factory = sessionmaker(bind=engine)
    session = factory()

    user = select_user(session=session)
    if user is None:
        print("\n* undefined user")
        return

    for user_lock in session.query(UserLock).filter_by(
        owner_id=user.id
    ).all():
        print()
        print(user_lock.creation_date, user_lock.reason)

        yes_or_no = input("* remove this request? [y/n] : ")
        if yes_or_no == "yes" or yes_or_no.lower() == "y":
            session.query(UserLock).filter_by(
                id=user_lock.id
            ).delete()

    session.commit()


if __name__ == "__main__":
    init_engine()
    main()
