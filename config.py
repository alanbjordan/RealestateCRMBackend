import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    db_url = os.getenv("DATABASE_URL")

    # Fix for older PostgreSQL URLs from Heroku
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")

    # CORS settings (Ensure it correctly loads multiple domains)
    CORS_ORIGINS = os.getenv("CORS_ORIGINS")
    CORS_SUPPORTS_CREDENTIALS = True
