from os import environ

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from dotenv import load_dotenv

from app.key import secret_key

db = SQLAlchemy()
migrate = Migrate()
redis = FlaskRedis()


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secret_key()
    app.config['SQLALCHEMY_DATABASE_URI'] = environ['SQLALCHEMY_DATABASE_URI']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_COOKIE_NAME'] = "slow_postbox"
    app.config['SESSION_COOKIE_SAMESITE'] = "Strict"
    app.config['REDIS_URL'] = environ['REDIS_URL']

    from key import get
    app.config['KEY_STORE'] = get()

    __import__("app.models")
    db.init_app(app=app)
    migrate.init_app(app=app, db=db)
    redis.init_app(app)

    from . import views
    for view in views.__all__:
        app.register_blueprint(getattr(getattr(views, view), "bp"))

    from flask import g
    from flask import session
    from flask import redirect
    from flask import url_for

    @app.before_request
    def before_request():
        # set global
        g.title = environ['TITLE']

    @app.after_request
    def after_request(response):
        response.headers['X-Frame-Options'] = "deny"
        return response

    @app.errorhandler(404)
    @app.errorhandler(405)
    def back_to_index(error):
        if 'user' in session:
            return redirect(url_for("dashboard.index"))

        return redirect(url_for("index.index"))

    return app
