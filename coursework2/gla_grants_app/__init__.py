import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Create a SQLAlchemy declarative base
class Base(DeclarativeBase):
    pass

# Create the SQLAlchemy object
db = SQLAlchemy(model_class=Base)

def create_app(test_config=None):
    # Create the Flask app
    app = Flask(__name__, instance_relative_config=True)
    
    # Configure the app
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, 'gla_grants.sqlite'),
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize the database
    db.init_app(app)

    with app.app_context():
        # Import and register the blueprint
        from coursework2.gla_grants_app.routes import main
        app.register_blueprint(main)
        
        # Create database tables
        db.create_all()
        
        # Import and setup data if database is empty
        from coursework2.gla_grants_app.helpers import setup_db_data
        setup_db_data()

    return app