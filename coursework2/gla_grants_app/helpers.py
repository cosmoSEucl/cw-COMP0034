import pandas as pd
import os
from werkzeug.security import generate_password_hash
from coursework2.gla_grants_app import db
from coursework2.gla_grants_app.models import Grant, User

def setup_db_data():
    """Setup database with initial data if it's empty"""
    # Check if grants table is empty
    if db.session.query(Grant).first() is None:
        # Load sample data from CSV
        try:
            # In a real implementation, you would use the actual GLA grants dataset
            # This is a placeholder for demonstration
            sample_data = [
                {
                    'title': 'Community Garden Project',
                    'description': 'Funding for creating community gardens in urban areas',
                    'amount_awarded': 25000.00,
                    'funding_org_department': 'Environment',
                    'recipient_org_name': 'Green London Initiative',
                    'category': 'Environment',
                    'award_date': '2023-06-15'
                },
                {
                    'title': 'Youth Sports Programme',
                    'description': 'Supporting sports activities for disadvantaged youth',
                    'amount_awarded': 35000.00,
                    'funding_org_department': 'Sports & Recreation',
                    'recipient_org_name': 'Active Youth London',
                    'category': 'Youth Services',
                    'award_date': '2023-05-22'
                },
                {
                    'title': 'Digital Skills for Seniors',
                    'description': 'Training programme to teach digital skills to seniors',
                    'amount_awarded': 18000.00,
                    'funding_org_department': 'Education',
                    'recipient_org_name': 'Age Connect London',
                    'category': 'Education',
                    'award_date': '2023-04-10'
                },
                {
                    'title': 'Arts Festival Funding',
                    'description': 'Support for local arts festival in East London',
                    'amount_awarded': 42000.00,
                    'funding_org_department': 'Culture',
                    'recipient_org_name': 'East London Arts Collective',
                    'category': 'Arts & Culture',
                    'award_date': '2023-07-05'
                },
                {
                    'title': 'Mental Health Support Services',
                    'description': 'Expanding mental health services in South London',
                    'amount_awarded': 65000.00,
                    'funding_org_department': 'Health',
                    'recipient_org_name': 'Mind London',
                    'category': 'Health',
                    'award_date': '2023-03-18'
                }
            ]
            
            # Add sample grants to database
            for item in sample_data:
                grant = Grant(**item)
                db.session.add(grant)
            
            # Check if admin user already exists
            admin_exists = db.session.query(User).filter_by(username='admin').first()
            if not admin_exists:
                # Add a sample admin user with hashed password
                admin_user = User(
                    username='admin',
                    password=generate_password_hash('admin_password'),
                    is_admin=True
                )
                db.session.add(admin_user)
            
            # Check if regular user already exists
            user_exists = db.session.query(User).filter_by(username='user').first()
            if not user_exists:
                # Add a sample regular user with hashed password
                regular_user = User(
                    username='user',
                    password=generate_password_hash('user_password'),
                    is_admin=False
                )
                db.session.add(regular_user)
            
            db.session.commit()
            print("Database setup complete with sample data and users")
        except Exception as e:
            print(f"Error setting up database: {e}")
            db.session.rollback()