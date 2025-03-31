"""
Helper functions for the GLA Grants application.

This module provides utility functions used throughout the application,
primarily for setting up initial database data.
"""
import pandas as pd
import os
from werkzeug.security import generate_password_hash
from coursework2.gla_grants_app import db
from coursework2.gla_grants_app.models import User

def setup_db_data():
    """
    Setup database with initial data if it's empty.
    
    This function checks if the users table is empty and adds sample
    admin and regular users with hashed passwords if needed.
    """
    if db.session.query(User).first() is None:
        try:
            admin_exists = db.session.query(User).filter_by(username='admin1').first()
            if not admin_exists:
                admin_user = User(
                    username='admin1',
                    password=generate_password_hash('admin1234'),
                    is_admin=True
                )
                db.session.add(admin_user)
            
            user_exists = db.session.query(User).filter_by(username='user2').first()
            if not user_exists:
                regular_user = User(
                    username='user2',
                    password=generate_password_hash('user1234'),
                    is_admin=False
                )
                db.session.add(regular_user)
            
            db.session.commit()
            print("Database setup complete with sample users")
        except Exception as e:
            print(f"Error setting up database: {e}")
            db.session.rollback()