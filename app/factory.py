"""
Kyro — Flask Application Factory

Creates and configures the Flask app with:
  • Blueprint registration
  • Global error handlers
  • Logging initialisation
"""

from __future__ import annotations

from flask import Flask, jsonify

from app.core.config import settings
from app.core.errors import KyroError
from app.core.logging import setup_logging, get_logger
from app.core.sockets import socketio


def create_app() -> Flask:
    """Application factory — returns a fully configured Flask app."""

    # Initialise logging first
    setup_logging()
    logger = get_logger("app")

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.flask.SECRET_KEY
    app.config["DEBUG"] = settings.flask.DEBUG

    # ---- Register Blueprints ----
    from app.routes.patient_routes import patient_bp
    from app.routes.doctor_routes import doctor_bp
    from app.routes.queue_routes import queue_bp
    from app.routes.health_routes import health_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.audit_routes import audit_bp
    from app.routes.model_routes import model_bp
    from app.routes.realtime_routes import realtime_bp
    from app.routes.ai_routes import ai_bp

    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(queue_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(model_bp)
    app.register_blueprint(realtime_bp)
    app.register_blueprint(ai_bp)

    # ---- Global Error Handlers ----
    @app.errorhandler(KyroError)
    def handle_kyro_error(error: KyroError):
        logger.warning("KyroError [%s]: %s", error.error_type, error.message)
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(404)
    def handle_404(_):
        return jsonify({"error": "NOT_FOUND", "message": "Resource not found."}), 404

    @app.errorhandler(405)
    def handle_405(_):
        return jsonify({"error": "METHOD_NOT_ALLOWED", "message": "HTTP method not allowed."}), 405

    @app.errorhandler(500)
    def handle_500(error):
        logger.exception("Unhandled 500 error: %s", error)
        return jsonify({"error": "INTERNAL_ERROR", "message": "An unexpected error occurred."}), 500

    # ---- Initialise Sockets ----
    socketio.init_app(app)

    logger.info("Kyro Flask app and SocketIO initialised successfully")
    return app
