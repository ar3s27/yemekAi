import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "devsecret"
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI") or "sqlite:///site.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
