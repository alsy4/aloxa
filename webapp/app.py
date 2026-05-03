from flask import Flask, redirect, request, url_for
from flask_wtf.csrf import CSRFProtect

from config import FLASK_SECRET_KEY
from medication import MedicationManager
from webapp.auth import is_authenticated
from webapp.broker import EventBroker

csrf = CSRFProtect()


def create_app(
    manager: MedicationManager | None = None,
    broker: EventBroker | None = None,
) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = FLASK_SECRET_KEY
    app.config["MANAGER"] = manager or MedicationManager()
    app.config["BROKER"] = broker or EventBroker()

    csrf.init_app(app)

    from webapp.auth import bp as auth_bp
    from webapp.routes import bp as routes_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(routes_bp)

    # SSE/JSON endpoints don't need CSRF (they're GET only)
    csrf.exempt(routes_bp.name + ".events")
    csrf.exempt(routes_bp.name + ".api_pending")

    _PUBLIC_ENDPOINTS = {"auth.login", "static"}

    @app.before_request
    def require_login():
        if request.endpoint in _PUBLIC_ENDPOINTS:
            return None
        if is_authenticated():
            return None
        return redirect(url_for("auth.login", next=request.path))

    return app
