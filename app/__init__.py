from os import environ

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

from app.key import secret_key

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secret_key()
    app.config['SQLALCHEMY_DATABASE_URI'] = environ['SQLALCHEMY_DATABASE_URI']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    __import__("app.models")
    db.init_app(app=app)
    migrate.init_app(app=app, db=db)

    from . import views
    for view in views.__all__:
        app.register_blueprint(getattr(getattr(views, view), "bp"))

    from flask import g
    from flask import request
    from flask import session
    from flask import redirect
    from flask import url_for

    @app.before_request
    def before_request():
        # set global
        g.title = environ['TITLE']

        # auth filter
        if request.path.startswith("/auth") and not request.path.endswith("logout"):
            if 'user' in session:
                return redirect(url_for("dashboard.index"))

    @app.after_request
    def after_request(response):
        response.headers['X-Frame-Options'] = "deny"

    @app.errorhandler(404)
    @app.errorhandler(405)
    def back_to_index(error):
        return redirect(url_for("index.index"))

    return app
