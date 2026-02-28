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

    # --- Alap config ---
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

    database_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- FONTOS: stabil RDS kapcsolat ---
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        # Megakadályozza a "stale connection" hibákat RDS-nél
        "pool_pre_ping": True,

        # Újrahasznosítás 5 perc után (RDS idle timeout ellen)
        "pool_recycle": 300,

        # Ne várjon percekig DB connectnél
        "connect_args": {
            "connect_timeout": 3
        },
    }

    # --- Init ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- Blueprint-ek ---
    from .routes_auth import auth_bp
    from .routes_photos import photos_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(photos_bp)

    # --- Egyszerű, biztos health endpoint ---
    @app.get("/health")
    def health():
        return "ok", 200

    return app