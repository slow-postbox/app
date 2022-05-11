from datetime import datetime
from datetime import timedelta

from sqlalchemy import func

from app import db


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

    password = db.Column(
        db.String(128),
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
        return f"<Code id={self.id} owner_id={self.owner_id}>"


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

    # max size = 20000
    content = db.Column(
        db.Text,
        nullable=False,
    )

    # True  =
    # False = Read, Write
    lock = db.Column(
        db.Boolean,
        nullable=True,
        default=False
    )

    def __repr__(self):
        return f"<Mail id={self.id} owner_id={self.owner_id}>"
