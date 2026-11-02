from flask import Flask

from .api import api_bp
from .store import AttendanceStore


def register_backend(app: Flask, store: AttendanceStore) -> None:
    app.config["ATTENDANCE_STORE"] = store
    app.register_blueprint(api_bp, url_prefix="/api")
