from datetime import datetime
from datetime import timedelta

from sqlalchemy import func
from mistune import create_markdown

from app import db


def get_html(text: str) -> str:
    _ = create_markdown(
        escape=False,
        renderer="html",
        plugins=[
            'strikethrough',
            'footnotes',
            'table',
            'task_lists',
        ]
    )
    return _(text)


class User(db.Model):
    id = db.Column(
        db.Integer,
        unique=True,
        primary_key=True,
        nullable=False
    )

    email = db.Column(
        db.String(96),
        unique=True,
        nullable=False
    )

    oauth = db.Column(
        db.String(10),
        nullable=False
    )

    oauth_id = db.Column(
        db.String(36),
        nullable=False
    )

    creation_date = db.Column(
        db.DateTime,
        nullable=False,
        default=func.now()
    )

    last_login = db.Column(
        db.DateTime,
        nullable=False,
        default=func.now()
    )

    tos = db.Column(
        db.Integer,
        nullable=False,
    )

    privacy = db.Column(
        db.Integer,
        nullable=False,
    )

    admin = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    def __repr__(self):
        return f"<User id={self.id} email={self.email!r}>"


class LoginHistory(db.Model):
    id = db.Column(
        db.Integer,
        unique=True,
        primary_key=True,
        nullable=False
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    ip = db.Column(
        db.String(120),
        nullable=False
    )

    creation_date = db.Column(
        db.DateTime,
        nullable=False,
        default=func.now()
    )

    def __repr__(self):
        return f"<LoginHistory id={self.id}>"


class Code(db.Model):
    id = db.Column(
        db.Integer,
        unique=True,
        primary_key=True,
        nullable=False
    )

    email = db.Column(
        db.String(96),
        nullable=False
    )

    # xxxx-xxxx
    code = db.Column(
        db.String(9),
        nullable=False
    )

    ip = db.Column(
        db.String(120),
        nullable=False
    )

    creation_date = db.Column(
        db.DateTime,
        nullable=False,
        default=func.now()
    )

    used_date = db.Column(
        db.DateTime,
        nullable=True,
        default=None
    )

    def is_used(self) -> bool:
        #   <used_date type>
        # None     : not used
        # Datetime : used
        return self.used_date is not None

    def is_expired(self) -> bool:
        return self.creation_date < datetime.now() - timedelta(minutes=3)

    def __repr__(self):
        return f"<Code id={self.id} email={self.email!r}>"


class Mail(db.Model):
    id = db.Column(
        db.Integer,
        unique=True,
        primary_key=True,
        nullable=False
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    creation_date = db.Column(
        db.DateTime,
        nullable=False,
        default=func.now()
    )

    send_date = db.Column(
        db.DateTime,
        nullable=True,
    )

    title = db.Column(
        db.String(100),
        nullable=False
    )

    # max size = 20000
    content = db.Column(
        db.Text,
        nullable=False,
    )

    # True  =
    # False = Read, Write
    lock = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    # True  = sent
    # False = not send
    status = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    # True  = read
    # False = not read
    read = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    @property
    def html(self) -> str:
        return get_html(text=self.content)

    def __repr__(self):
        return f"<Mail id={self.id} owner_id={self.owner_id}>"


class Notice(db.Model):
    id = db.Column(
        db.Integer,
        unique=True,
        primary_key=True,
        nullable=False
    )

    creation_date = db.Column(
        db.DateTime,
        nullable=False,
        default=func.now()
    )

    title = db.Column(
        db.String(100),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False,
    )

    @property
    def html(self) -> str:
        return get_html(text=self.content)

    def __repr__(self):
        return f"<Notice id={self.id} title={self.title!r}>"


class TermsOfService(db.Model):
    id = db.Column(
        db.Integer,
        unique=True,
        primary_key=True,
        nullable=False
    )

    creation_date = db.Column(
        db.DateTime,
        nullable=False,
        default=func.now()
    )

    content = db.Column(
        db.Text,
        nullable=False,
    )

    @property
    def html(self) -> str:
        return get_html(text=self.content)

    @property
    def effective_date(self) -> datetime:
        return self.creation_date + timedelta(days=7)

    def __repr__(self):
        return f"<TermsOfService id={self.id} title={self.title!r}>"


class PrivacyPolicy(db.Model):
    id = db.Column(
        db.Integer,
        unique=True,
        primary_key=True,
        nullable=False
    )

    creation_date = db.Column(
        db.DateTime,
        nullable=False,
        default=func.now()
    )

    content = db.Column(
        db.Text,
        nullable=False,
    )

    @property
    def html(self) -> str:
        return get_html(text=self.content)

    @property
    def effective_date(self) -> datetime:
        return self.creation_date + timedelta(days=7)

    def __repr__(self):
        return f"<PrivacyPolicy id={self.id} title={self.title!r}>"


class UserLock(db.Model):
    id = db.Column(
        db.Integer,
        unique=True,
        primary_key=True,
        nullable=False
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    creation_date = db.Column(
        db.DateTime,
        nullable=False,
        default=func.now()
    )

    reason = db.Column(
        db.Text,
        nullable=False
    )

    def __repr__(self):
        return f"<UserLock id={self.id} owner_id={self.owner_id}>"
