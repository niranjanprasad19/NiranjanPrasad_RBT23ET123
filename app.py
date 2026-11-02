from flask import Flask, render_template

from backend import register_backend
from backend.store import AttendanceStore


def create_app() -> Flask:
    app = Flask(__name__)
    register_backend(app, AttendanceStore())

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


app = create_app()


def main() -> None:
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
