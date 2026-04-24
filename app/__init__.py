"""
Application factory for the Intelligence Query Engine.

Usage
-----
    from app import create_app
    app = create_app()          # defaults to "development"
    app = create_app("testing") # uses TestingConfig
"""

from __future__ import annotations

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from app.config import config
from app.extensions import init_db


def create_app(config_name: str = "development") -> Flask:
    """Create and configure a Flask application instance.

    Parameters
    ----------
    config_name:
        One of ``"development"``, ``"testing"``, ``"production"``, or
        ``"default"``.  Selects the matching entry from ``app.config.config``.

    Returns
    -------
    Flask
        A fully configured Flask application ready to serve requests.
    """
    # Load .env before reading any config values (no-op if already loaded).
    load_dotenv()

    app = Flask(__name__)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    app.config.from_object(config[config_name])

    # ------------------------------------------------------------------
    # Extensions
    # ------------------------------------------------------------------
    # Enable CORS for all /api/* routes, allowing any origin.
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialise the SQLAlchemy engine and attach it to app.extensions.
    init_db(app)

    # ------------------------------------------------------------------
    # Blueprints
    # ------------------------------------------------------------------
    # These imports are placed here (inside the factory) to avoid circular
    # imports.  The blueprint modules will be created in subsequent tasks;
    # the imports are written normally and will be satisfied once those
    # files exist.
    from app.blueprints.profiles import profiles_bp  # noqa: PLC0415
    from app.blueprints.search import search_bp       # noqa: PLC0415

    app.register_blueprint(profiles_bp, url_prefix="/api")
    app.register_blueprint(search_bp, url_prefix="/api")

    # ------------------------------------------------------------------
    # Error handlers
    # ------------------------------------------------------------------
    register_error_handlers(app)

    return app


def register_error_handlers(app: Flask) -> None:
    """Register global JSON error handlers on *app*.

    Handlers for 400, 422, 500, and 502 are registered here.  The 500
    handler is the only one fully implemented at this stage (Task 2.3);
    the remaining handlers will be fleshed out in Task 11.
    """

    @app.errorhandler(400)
    def bad_request(e):
        description = getattr(e, "description", "Invalid query parameters")
        return jsonify({"status": "error", "message": str(description)}), 400

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({"status": "error", "message": "Invalid parameter type"}), 422

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"status": "error", "message": "Server failure"}), 500

    @app.errorhandler(502)
    def bad_gateway(e):
        return jsonify({"status": "error", "message": "Server failure"}), 502
