from flask import Blueprint

import post

bp = Blueprint("post", __name__, url_prefix="/post")

for p in post.__all__:
    bp.register_blueprint(getattr(getattr(post, p), "bp"))
