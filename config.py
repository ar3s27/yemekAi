import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bu-cok-gizli-bir-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///yemekai.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
