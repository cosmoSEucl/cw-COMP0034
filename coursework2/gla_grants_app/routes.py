from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from coursework2.gla_grants_app import db
from coursework2.gla_grants_app.models import Grant, User, GrantApplication
from coursework2.gla_grants_app.forms import ApplicationForm, LoginForm, RegistrationForm
from sqlalchemy import func
import plotly.express as px
import pandas as pd

# Create blueprint
main = Blueprint('main', __name__)

@main.route('/')
def landing():
    """Landing page with sign in and create account options"""
    # Make sure there are no access controls here that might restrict access
    return render_template('landing.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    """Login page route"""
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
        
        if user:
            print(f"User found: {user.username}, Checking password...")
            if check_password_hash(user.password, password):
                print("Password check successful!")
                session['user_id'] = user.id
                session['is_admin'] = user.is_admin
                flash('Logged in successfully!', 'success')
                return redirect(url_for('main.index'))
            else:
                print("Password check failed!")
        else:
            print(f"No user found with username: {username}")
            
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@main.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page route"""
    print("Register route accessed")  # Debug print
    form = RegistrationForm()
    
    print(f"Form created: {form}")  # Debug print
    
    if form.validate_on_submit():
        print("Form validated")  # Debug print
        username = form.username.data
        password = form.password.data
        
        # Check if username already exists
        existing_user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
        
        if existing_user:
            flash('Username already exists', 'danger')
        else:
            # Create new user
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password, is_admin=False)
            db.session.add(new_user)
            db.session.commit()
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('main.login'))
    
    print(f"Form errors: {form.errors}")  # Debug print
    return render_template('register.html', form=form)

@main.route('/logout')
def logout():
    """Logout route"""
    session.pop('user_id', None)
    session.pop('is_admin', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('main.landing'))

@main.route('/home')
def index():
    """Home page route"""
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('main.login'))
        
    return render_template('index.html')

# Add login required check to other routes
@main.route('/dash-visualization')
def dash_visualization():
    """Route to redirect directly to the Dash app"""
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('main.login'))
        
    # Redirect directly to the Dash app URL
    return redirect('/dash/')

@main.route('/grants-dataset')
def grants_dataset():
    """Grant dataset browsing page route"""
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('main.login'))
        
    # Get grants data from database
    grants = db.session.execute(db.select(Grant)).scalars().all()
    return render_template('grants_dataset.html', grants=grants)

@main.route('/submit-application', methods=['GET', 'POST'])
def submit_application():
    """Submit application page route"""
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('main.login'))
        
    form = ApplicationForm()
    
    if form.validate_on_submit():
        # Create new application from form data
        application = GrantApplication(
            user_id=session['user_id'],  # Use the logged-in user's ID
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            question=form.question.data,
            date_submitted=pd.Timestamp.now().strftime('%Y-%m-%d')
        )
        
        # Add to database
        db.session.add(application)
        db.session.commit()
        
        flash('Your application has been submitted successfully!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('submit_application.html', form=form)

@main.route('/admin-dashboard')
def admin_dashboard():
    """Admin dashboard route"""
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('main.login'))
        
    if not session.get('is_admin', False):
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('main.index'))
        
    # Get submitted applications from database
    applications = db.session.execute(db.select(GrantApplication)).scalars().all()
    return render_template('admin_dashboard.html', applications=applications)

@main.route('/admin-review/<int:application_id>', methods=['POST'])
def admin_review(application_id):
    """Admin review submission route"""
    if 'user_id' not in session or not session.get('is_admin', False):
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('main.index'))
        
    # Get application
    application = db.get_or_404(GrantApplication, application_id)
    
    # Update comment
    application.comment = request.form.get('comment')
    db.session.commit()
    
    flash('Feedback submitted successfully!', 'success')
    return redirect(url_for('main.admin_dashboard'))