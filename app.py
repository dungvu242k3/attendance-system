from flask import Flask
from flask_cors import CORS

from config import Config
from routes.admin import admin_bp
from routes.api import api_bp
from routes.user import user_bp


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    CORS(app)
    app.config.from_object(Config)

    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(api_bp, url_prefix="/api")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=False)
