import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

    database_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    engine_opts = {}

    if database_url.startswith("postgresql"):
        engine_opts = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "connect_args": {
                "connect_timeout": 5,
            },
        }

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_opts

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .routes_auth import auth_bp
    from .routes_photos import photos_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(photos_bp)

    return app