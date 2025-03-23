"""
Combined test file for testing the GLA Grants Flask application.
Contains both fixtures and tests in a single file.
"""
import pytest
import os
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash
from coursework2.app import app as flask_app
from coursework2.gla_grants_app import db
from coursework2.gla_grants_app.models import User, Grant, GrantApplication

# =========================================================
# FIXTURES
# =========================================================

@pytest.fixture()
def app():
    """
    Use the actual Flask application instance for testing.
    This is the same app that is run with app.py
    """
    # Configure the app for testing
    flask_app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,  # Disable CSRF protection for testing
    })
    
    yield flask_app


@pytest.fixture()
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture()
def runner(app):
    """Create a test CLI runner for the app."""
    return app.test_cli_runner()


@pytest.fixture()
def db_session(app):
    """
    Create a database session for testing that will roll back changes.
    This ensures tests don't permanently modify the database.
    """
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Get session for testing
        session = db.session
        
        yield session
        
        # Rollback transaction after test
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def logged_in_user(client, db_session):
    """Create a logged-in regular user for testing."""
    # Create a unique username for this test run to avoid conflicts
    unique_username = f"testuser_{uuid.uuid4().hex[:8]}"
    
    # Create a test user
    hashed_password = generate_password_hash('testpassword')
    test_user = User(username=unique_username, password=hashed_password, is_admin=False)
    db_session.add(test_user)
    db_session.commit()
    
    # Log in the user
    client.post(
        '/login',
        data={'username': unique_username, 'password': 'testpassword'},
        follow_redirects=True
    )
    
    return test_user


@pytest.fixture()
def logged_in_admin(client, db_session):
    """Create a logged-in admin user for testing."""
    # Create a unique username for this test run to avoid conflicts
    unique_username = f"adminuser_{uuid.uuid4().hex[:8]}"
    
    # Create an admin user
    hashed_password = generate_password_hash('adminpassword')
    admin_user = User(username=unique_username, password=hashed_password, is_admin=True)
    db_session.add(admin_user)
    db_session.commit()
    
    # Log in the admin
    client.post(
        '/login',
        data={'username': unique_username, 'password': 'adminpassword'},
        follow_redirects=True
    )
    
    return admin_user

# =========================================================
# TESTS
# =========================================================

def test_landing_page(client):
    """
    GIVEN a Flask test client
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid and contains the expected content
    """
    response = client.get('/')
    assert response.status_code == 200
    assert b'Greater London Authority Grants' in response.data
    assert b'Sign In' in response.data
    assert b'Register' in response.data


def test_login_functionality(client, db_session):
    """
    GIVEN a Flask test client and a test user
    WHEN the '/login' page is posted to with valid credentials
    THEN check that the user is logged in and redirected to the index page
    """
    # Create a unique username for this test
    unique_username = f"loginuser_{uuid.uuid4().hex[:8]}"
    
    # Create a test user
    hashed_password = generate_password_hash('testpassword')
    test_user = User(username=unique_username, password=hashed_password, is_admin=False)
    db_session.add(test_user)
    db_session.commit()

    # Attempt login with valid credentials
    response = client.post(
        '/login',
        data={'username': unique_username, 'password': 'testpassword'},
        follow_redirects=True
    )
    
    assert response.status_code == 200
    assert b'Logged in successfully!' in response.data
    
    # Attempt login with invalid credentials
    response = client.post(
        '/login',
        data={'username': unique_username, 'password': 'wrongpassword'},
        follow_redirects=True
    )
    
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


def test_register_functionality(client, db_session):
    """
    GIVEN a Flask test client
    WHEN the '/register' page is posted to with valid data
    THEN check that a new user is created and user is redirected to login
    """
    # Test GET request to register page
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Create Account' in response.data
    
    # Create a unique username for this test
    unique_username = f"newuser_{uuid.uuid4().hex[:8]}"
    
    # Test successful registration
    response = client.post(
        '/register',
        data={
            'username': unique_username,
            'password': 'newpassword',
            'confirm_password': 'newpassword'
        },
        follow_redirects=True
    )
    
    assert response.status_code == 200
    assert b'Account created successfully! Please log in.' in response.data
    
    # Verify user was added to database
    user = db_session.query(User).filter_by(username=unique_username).first()
    assert user is not None
    assert user.is_admin is False
    
    # Test registration with existing username
    response = client.post(
        '/register',
        data={
            'username': unique_username,
            'password': 'anotherpassword',
            'confirm_password': 'anotherpassword'
        },
        follow_redirects=True
    )
    
    assert response.status_code == 200
    assert b'Username already exists' in response.data


def test_logout(client, logged_in_user):
    """
    GIVEN a Flask test client and a logged-in user
    WHEN the '/logout' page is requested
    THEN check that the user is logged out and redirected to the landing page
    """
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Logged out successfully' in response.data
    
    # After logout, accessing a protected page should redirect to login
    response = client.get('/home', follow_redirects=True)
    assert b'Please log in to access this page' in response.data


def test_home_page(client, logged_in_user):
    """
    GIVEN a Flask test client
    WHEN the '/home' page is requested with and without authentication
    THEN check the appropriate responses
    """
    # Authenticated request
    response = client.get('/home', follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome to GLA Grants' in response.data
    
    # Logout
    client.get('/logout')
    
    # Unauthenticated request
    response = client.get('/home', follow_redirects=True)
    assert b'Please log in to access this page' in response.data
    assert b'Sign In' in response.data


def test_dash_visualization(client, logged_in_user):
    """
    GIVEN a Flask test client
    WHEN the '/dash-visualization' page is requested
    THEN check that the response contains the dashboard iframe
    """
    response = client.get('/dash-visualization', follow_redirects=True)
    assert response.status_code == 200
    assert b'Advanced Data Visualization' in response.data
    assert b'iframe' in response.data
    assert b'src="/dash/"' in response.data


def test_submit_application(client, logged_in_user, db_session):
    """
    GIVEN a Flask test client and a logged-in user
    WHEN the '/submit-application' page is accessed and posted to
    THEN check appropriate responses and database updates
    """
    # Test GET request
    response = client.get('/submit-application', follow_redirects=True)
    assert response.status_code == 200
    assert b'Submit Application Snippet' in response.data
    assert b'Title' in response.data
    
    # Test POST request
    response = client.post(
        '/submit-application',
        data={
            'title': f'Test Application {uuid.uuid4().hex[:8]}',
            'description': 'This is a test application description.',
            'category': 'Community',
            'question': 'Test question for the application?'
        },
        follow_redirects=True
    )
    
    assert response.status_code == 200
    assert b'Your application has been submitted successfully!' in response.data
    
    # Verify application was added to database
    application = db_session.query(GrantApplication).filter_by(description='This is a test application description.').first()
    assert application is not None
    assert application.description == 'This is a test application description.'


def test_admin_dashboard(client, logged_in_admin):
    """
    GIVEN a Flask test client and a logged-in admin user
    WHEN the '/admin-dashboard' page is requested
    THEN check that the response contains the admin dashboard
    """
    # Admin access
    response = client.get('/admin-dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Admin Dashboard' in response.data


def test_admin_review(client, logged_in_admin, db_session):
    """
    GIVEN a Flask test client, logged-in admin, and an application
    WHEN the '/admin-review/<id>' endpoint is posted to
    THEN check that the application is updated with the comment
    """
    # Create a test application
    test_application = GrantApplication(
        user_id=logged_in_admin.id,  # Use the admin's user ID
        title=f'Test Application {uuid.uuid4().hex[:8]}',
        description='Application description',
        category='Community',
        question='Application question',
        date_submitted=datetime.now().strftime('%Y-%m-%d')
    )
    db_session.add(test_application)
    db_session.commit()
    
    application_id = test_application.id
    
    response = client.post(
        f'/admin-review/{application_id}',
        data={'comment': 'This is admin feedback on the application.'},
        follow_redirects=True
    )
    
    assert response.status_code == 200
    assert b'Feedback submitted successfully!' in response.data
    
    # Verify application was updated
    updated_application = db_session.query(GrantApplication).get(application_id)
    assert updated_application.comment == 'This is admin feedback on the application.'


def test_account_page(client, logged_in_user):
    """
    GIVEN a Flask test client and a logged-in user
    WHEN the '/account' page is requested
    THEN check that the response contains the account information
    """
    response = client.get('/account', follow_redirects=True)
    assert response.status_code == 200
    assert b'My Profile' in response.data
    assert b'Change Password' in response.data


def test_account_password_change(client, logged_in_user, db_session):
    """
    GIVEN a Flask test client and a logged-in user
    WHEN the '/account' page is posted to with valid password change data
    THEN check that the password is updated
    """
    # Get the user's current password hash to verify it changes
    user = db_session.query(User).get(logged_in_user.id)
    old_password_hash = user.password
    
    response = client.post(
        '/account',
        data={
            'old_password': 'testpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        },
        follow_redirects=True
    )
    
    assert response.status_code == 200
    assert b'Your password has been updated successfully!' in response.data
    
    # Verify password was updated
    user = db_session.query(User).get(logged_in_user.id)
    assert user.password != old_password_hash


def test_news_page(client, logged_in_user):
    """
    GIVEN a Flask test client and a logged-in user
    WHEN the '/news' page is requested
    THEN check that the response contains the news content
    """
    response = client.get('/news', follow_redirects=True)
    assert response.status_code == 200
    assert b'Latest Grant News' in response.data


def test_404_error(client):
    """
    GIVEN a Flask test client
    WHEN a non-existent route is requested
    THEN check that a 404 error is returned
    """
    response = client.get('/nonexistent-route')
    assert response.status_code == 404