import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-in-prod")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    DATABASE_URL = os.environ.get("DATABASE_URL", "loja.db")
