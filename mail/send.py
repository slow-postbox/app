from os import environ

from smtplib import SMTP
from email.mime.text import MIMEText

if 'SMTP_HOST' not in environ:
    from dotenv import load_dotenv
    load_dotenv()

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
