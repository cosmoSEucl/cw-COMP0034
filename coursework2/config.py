import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///your_database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
