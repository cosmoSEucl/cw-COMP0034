import pandas as pd
import os
from werkzeug.security import generate_password_hash
from coursework2.gla_grants_app import db
from coursework2.gla_grants_app.models import User  # Remove Grant import

def setup_db_data():
    """Setup database with initial data if it's empty"""
    # Check if users table is empty
    if db.session.query(User).first() is None:
        try:
            # Check if admin user already exists
            admin_exists = db.session.query(User).filter_by(username='admin1').first()
            if not admin_exists:
                # Add a sample admin user with hashed password
                admin_user = User(
                    username='admin1',
                    password=generate_password_hash('admin1234'),
                    is_admin=True
                )
                db.session.add(admin_user)
            
            # Check if regular user already exists
            user_exists = db.session.query(User).filter_by(username='user2').first()
            if not user_exists:
                # Add a sample regular user with hashed password
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