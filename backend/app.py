"""
Heart Disease Prediction Full-Stack Flask Application.
Application Factory, Blueprints Registration, Database Initialization, and Middleware Setup.
"""
import os
import sys

# Ensure repository root is on sys.path when app.py is invoked directly as a script
_repo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _repo_dir not in sys.path:
    sys.path.insert(0, _repo_dir)

if __package__ is None or __package__ == "":
    __package__ = "backend"

from flask import Flask, send_from_directory, render_template_string
from .config import get_config, config_by_name
from .extensions import cors
from .database.mongodb import init_db
from .database.indexes import create_database_indexes
from .routes import register_blueprints
from .middleware.security import add_security_headers
from .utils.responses import error_response

def create_app(config_name=None):
    """
    Flask Application Factory.
    """
    app = Flask(__name__, static_folder="../frontend", static_url_path="")

    # Load configuration
    if config_name and config_name in config_by_name:
        app.config.from_object(config_by_name[config_name])
    else:
        app.config.from_object(get_config())

    # Configure CORS with credentials support for session cookies
    cors_origin = app.config.get("FRONTEND_ORIGIN", "*")
    cors.init_app(
        app,
        supports_credentials=True,
        resources={r"/api/*": {"origins": cors_origin}}
    )

    # Initialize Database & Indexes
    with app.app_context():
        try:
            db = init_db(app)
            create_database_indexes(db)
        except Exception as e:
            app.logger.warning(f"Database initialization deferred or errored: {e}")

    # Register Blueprints
    register_blueprints(app)

    # Attach Security Headers
    @app.after_request
    def security_headers_hook(response):
        return add_security_headers(response)

    # Global Error Handlers
    @app.errorhandler(400)
    def handle_bad_request(e):
        return error_response(message="Bad Request. Please verify your input parameters.", status_code=400)

    @app.errorhandler(404)
    def handle_not_found(e):
        # If API route, return JSON; otherwise serve 404.html
        from flask import request
        if request.path.startswith("/api/"):
            return error_response(message="API resource not found.", status_code=404)
        frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
        page_404 = os.path.join(frontend_dir, "404.html")
        if os.path.exists(page_404):
            return send_from_directory(frontend_dir, "404.html"), 404
        return error_response(message="Page not found.", status_code=404)

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return error_response(message="HTTP Method not allowed for this route.", status_code=405)

    @app.errorhandler(500)
    def handle_internal_server_error(e):
        app.logger.error(f"Internal server error: {e}")
        return error_response(
            message="Internal server error. Please try again later.",
            error_code="INTERNAL_ERROR",
            status_code=500
        )

    # Frontend serving helper routes for full convenience
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

    @app.route("/")
    def index():
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/<path:filename>")
    def serve_frontend_page(filename):
        target = os.path.join(frontend_dir, filename)
        if os.path.exists(target):
            return send_from_directory(frontend_dir, filename)
        # Check if .html extension was omitted
        if os.path.exists(f"{target}.html"):
            return send_from_directory(frontend_dir, f"{filename}.html")
        return send_from_directory(frontend_dir, "404.html"), 404

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", True))
