from os import environ

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import TermsOfService
from app.models import PrivacyPolicy

if __name__ == "__main__":
    load_dotenv()
    engine = create_engine(environ.get("SQLALCHEMY_DATABASE_URI"))
    session_factory = sessionmaker(bind=engine)

    session = session_factory()

    if session.query(TermsOfService).count() == 0:
        tos = TermsOfService()
        tos.content = "임시로 생성된 서비스 이용약관 입니다."
        session.add(tos)
        print("임시 서비스 이용약관을 등록합니다.")
    else:
        print("등록된 서비스 이용약관이 있습니다.")

    if session.query(PrivacyPolicy).count() == 0:
        privacy = PrivacyPolicy()
        privacy.content = "임시로 생성된 개인정보 처리방침 입니다."
        session.add(privacy)
        print("임시 개인정보 처리방침을 등록합니다.")
    else:
        print("등록된 개인정보 처리방침이 있습니다.")

    session.commit()
