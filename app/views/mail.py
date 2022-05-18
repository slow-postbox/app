from flask import Blueprint

import mail

bp = Blueprint("mail", __name__, url_prefix="/mail")

for p in mail.__all__:
    bp.register_blueprint(getattr(getattr(mail, p), "bp"))
