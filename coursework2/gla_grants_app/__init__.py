"""
Initialization module for the GLA Grants application.

This module sets up the Flask application, configures the SQLAlchemy database,
and registers all the necessary components such as routes, models, and the Dash
application. It creates a factory function for the Flask application that can
be used for both development and testing environments.
"""
import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import secrets

class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""
    pass

db = SQLAlchemy(model_class=Base)

def create_app(test_config=None):
    """
    Create and configure the Flask application.
    
    Args:
        test_config (dict, optional): Configuration dictionary for testing.
            Defaults to None.
    
    Returns:
        Flask: The configured Flask application.
    """
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY=secrets.token_hex(16),
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, 'gla_grants.sqlite'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    
    with app.app_context():
        from coursework2.gla_grants_app.routes import main
        app.register_blueprint(main)

        @app.errorhandler(404)
        def page_not_found(e):
            return render_template('errors/404.html'), 404
            
        @app.errorhandler(500)
        def internal_server_error(e):
            return render_template('errors/500.html'), 500
        
        db.create_all()
        
        from coursework2.gla_grants_app.helpers import setup_db_data
        setup_db_data()
        
        from coursework2.gla_grants_app.dash_app import init_dash
        init_dash(app)

    return app