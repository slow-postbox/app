from os import environ

from smtplib import SMTP
from email.mime.text import MIMEText

SMTP_HOST = environ['SMTP_HOST']
SMTP_PORT = int(environ['SMTP_PORT'])
SMTP_USER = environ['SMTP_USER']
SMTP_PASSWORD = environ['SMTP_PASSWORD']


def send_token(email: str, code: str, ip: str):
    html = "\n".join([
        f"<h1>{code}</h1>",
        f"<p>인증 코드는 3분후 만료됩니다.</p>",
        "<br>",
        "<br>",
        f"<p>요청 IP : {ip}</p>",
    ])

    payload = MIMEText(html, "html", "utf-8")
    payload['From'] = SMTP_USER
    payload['Subject'] = f"{environ['TITLE']} - 이메일 인증 코드"

    with SMTP(SMTP_HOST, SMTP_PORT) as client:
        client.starttls()
        client.login(
            user=SMTP_USER,
            password=SMTP_PASSWORD
        )

        client.sendmail(
            from_addr=SMTP_USER,
            to_addrs=[email],
            msg=payload.as_string()
        )


def send_password_reset(email: str, url: str):
    html = "\n".join([
        f"<h1>{environ['title']}</h1>",
        "<br>",
        f"<p><a href=\"{url}\" target=\"_blank\">다음 링크</a>로 접속해 비밀번호를 재설정 해주세요.</p>",
        "<p>해당 비밀번호 재설정 요청은 5분뒤 만료됩니다.</p>",
    ])

    payload = MIMEText(html, "html", "utf-8")
    payload['From'] = SMTP_USER
    payload['Subject'] = f"[{environ['TITLE']}] 비밀번호 재설정"

    with SMTP(SMTP_HOST, SMTP_PORT) as client:
        client.starttls()
        client.login(
            user=SMTP_USER,
            password=SMTP_PASSWORD
        )

        client.sendmail(
            from_addr=SMTP_USER,
            to_addrs=[email],
            msg=payload.as_string()
        )
