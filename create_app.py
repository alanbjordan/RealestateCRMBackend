from flask import Flask
from flask_cors import CORS
from config import Config
from database import db, bcrypt
import os


def create_app():
    app = Flask(__name__)

    # Apply configuration from Config class
    app.config.from_object(Config)

    # Initialize SQLAlchemy and Bcrypt with the app instance
    db.init_app(app)
    bcrypt.init_app(app)

    #    # Fetch allowed origins from environment variable and split them into a list
    allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")  # Split by comma

    # Setup CORS configuration (Now supports multiple origins)
    CORS(
        app,
        supports_credentials=True,
        resources={r"/*": {"origins": allowed_origins}}
    )

    return app
