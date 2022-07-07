from os import environ
from logging import getLogger

from flask import Flask
from flask import Blueprint
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from dotenv import load_dotenv

from app.key import secret_key

db = SQLAlchemy()
migrate = Migrate()
redis = FlaskRedis()
logger = getLogger()


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secret_key()
    app.config['SQLALCHEMY_DATABASE_URI'] = environ['SQLALCHEMY_DATABASE_URI']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_COOKIE_NAME'] = "slow_postbox"
    app.config['SESSION_COOKIE_SAMESITE'] = "Lax"
    app.config['REDIS_URL'] = environ['REDIS_URL']

    from key import get
    app.config['KEY_STORE'] = get()

    __import__("app.models")
    db.init_app(app=app)
    migrate.init_app(app=app, db=db)
    redis.init_app(app)

    from . import views
    for view in views.__all__:
        app.register_blueprint(getattr(views, view).bp)

    social = Blueprint("social", "social", url_prefix="/social")

    for service in [__import__(x) for x in [
        "kakao",
    ]]:
        sbp = Blueprint(service.__name__, service.__name__, url_prefix=f"/{service.__name__}")
        for x in [getattr(service, x).bp for x in service.__all__]:
            sbp.register_blueprint(blueprint=x)

        social.register_blueprint(sbp)

    app.register_blueprint(social)

    from app import template_filters
    for template_filter in [
        getattr(template_filters, x)
        for x in dir(template_filters)
        if not x.startswith("_")
    ]:
        app.add_template_filter(f=template_filter)

    from flask import g
    from flask import session
    from flask import redirect
    from flask import url_for

    @app.before_request
    def before_request():
        # set global
        g.title = environ['TITLE']
        g.host = environ['HOST']

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
