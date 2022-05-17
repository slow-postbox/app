from os import environ

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from app.models import User

engine = None


def init_engine():
    load_dotenv()
    globals().update({
        "engine": create_engine(environ.get("SQLALCHEMY_DATABASE_URI"))
    })


def select_user(session) -> User:
    print("\n* select user to upgrade permission *\n")
    user_id = int(input("(int) user_id : "))
    user = session.query(User).filter_by(
        id=user_id
    ).first()

    print("\n* selected user is", user.email)
    return user


def main():
    factory = sessionmaker(bind=engine)
    session = factory()

    user = select_user(session=session)
    if user is None:
        print("\n* undefined user")
        return

    if user.admin is True:
        print("\n* admin -> normal user")
        user.admin = False
    else:
        print("\n* normal user -> admin")
        user.admin = True

    session.commit()
    print("\n* database updated")


if __name__ == "__main__":
    init_engine()
    main()
