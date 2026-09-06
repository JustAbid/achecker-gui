"""Application factory for the AChecker web interface."""

import os

from flask import Flask, url_for

from .config import Config
from .store import HistoryStore
from .views import bp

__all__ = ["create_app"]


def create_app(config=None, store=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    upload_folder = app.config.get("UPLOAD_FOLDER") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads"
    )
    app.config["UPLOAD_FOLDER"] = upload_folder
    os.makedirs(upload_folder, exist_ok=True)

    if store is None:
        store = HistoryStore(
            app.config["MONGO_URI"], app.config["MONGO_DB"], app.config["TIMEZONE"]
        )
    app.extensions["history_store"] = store

    @app.after_request
    def _no_store(response):
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.context_processor
    def _assets():
        def static_url(filename):
            try:
                version = int(os.path.getmtime(os.path.join(app.static_folder, filename)))
            except OSError:
                version = 0
            return url_for("static", filename=filename, v=version)

        return {"static_url": static_url}

    app.register_blueprint(bp)
    return app
