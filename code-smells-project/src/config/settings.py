import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-in-production')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'loja.db')
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
