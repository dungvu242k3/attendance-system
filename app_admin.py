from flask import Flask, redirect, url_for
from flask_cors import CORS

from config import Config
from routes.admin import admin_bp


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    CORS(app)
    app.config.from_object(Config)

    app.register_blueprint(admin_bp, url_prefix="/")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
