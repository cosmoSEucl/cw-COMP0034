"""
Routes module for the GLA Grants application.

This module defines all the URL routes for the Flask application, including
routes for landing, login, registration, dashboard, application submission,
and administrative functions.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from coursework2.gla_grants_app import db
from coursework2.gla_grants_app.models import User, GrantApplication
from coursework2.gla_grants_app.forms import ApplicationForm, LoginForm, RegistrationForm, PasswordChangeForm
from sqlalchemy import func
import plotly.express as px
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

main = Blueprint('main', __name__)

@main.route('/')
def landing():
    """
    Landing page with sign in and create account options.
    
    Returns:
        str: Rendered HTML template for the landing page.
    """
    return render_template('landing.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login page route.
    
    Handles user authentication using the LoginForm.
    
    Returns:
        str: Rendered HTML template for login or redirect to home page.
    """
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
    """
    Registration page route.
    
    Handles user registration using the RegistrationForm.
    
    Returns:
        str: Rendered HTML template for registration or redirect to login page.
    """
    print("Register route accessed")
    form = RegistrationForm()
    
    print(f"Form created: {form}")
    
    if form.validate_on_submit():
        print("Form validated")
        username = form.username.data
        password = form.password.data
        
        existing_user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
        
        if existing_user:
            flash('Username already exists', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password, is_admin=False)
            db.session.add(new_user)
            db.session.commit()
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('main.login'))
    
    print(f"Form errors: {form.errors}")
    return render_template('register.html', form=form)

@main.route('/logout')
def logout():
    """
    Logout route.
    
    Clears the user session and redirects to the landing page.
    
    Returns:
        Response: Redirect to the landing page.
    """
    session.pop('user_id', None)
    session.pop('is_admin', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('main.landing'))

@main.route('/home')
def index():
    """
    Home page route.
    
    The main dashboard page for logged-in users.
    
    Returns:
        str: Rendered HTML template for the home page or redirect to login page.
    """
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('main.login'))
        
    return render_template('index.html')

@main.route('/dash-visualization')
def dash_visualization():
    """
    Route to display Dash app within Flask template.
    
    Renders a template with an iframe that embeds the Dash application.
    
    Returns:
        str: Rendered HTML template with Dash visualization or redirect to login page.
    """
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('main.login'))
        
    return render_template('dash_visualization.html')

@main.route('/submit-application', methods=['GET', 'POST'])
def submit_application():
    """
    Submit application page route.
    
    Handles submission of grant applications using the ApplicationForm.
    
    Returns:
        str: Rendered HTML template for application submission or 
             redirect to home page after successful submission.
    """
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('main.login'))
        
    form = ApplicationForm()
    
    if form.validate_on_submit():
        application = GrantApplication(
            user_id=session['user_id'],
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            question=form.question.data,
            date_submitted=pd.Timestamp.now().strftime('%Y-%m-%d')
        )
        
        db.session.add(application)
        db.session.commit()
        
        flash('Your application has been submitted successfully!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('submit_application.html', form=form)

@main.route('/admin-dashboard')
def admin_dashboard():
    """
    Admin dashboard route.
    
    Displays all submitted applications for admin review.
    
    Returns:
        str: Rendered HTML template for admin dashboard or redirect if not authorized.
    """
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('main.login'))
        
    if not session.get('is_admin', False):
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('main.index'))
        
    applications = db.session.execute(db.select(GrantApplication)).scalars().all()
    return render_template('admin_dashboard.html', applications=applications)

@main.route('/admin-review/<int:application_id>', methods=['POST'])
def admin_review(application_id):
    """
    Admin review submission route.
    
    Handles submission of admin feedback on grant applications.
    
    Args:
        application_id (int): ID of the application being reviewed.
    
    Returns:
        Response: Redirect to admin dashboard after successful review submission.
    """
    if 'user_id' not in session or not session.get('is_admin', False):
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('main.index'))
        
    application = db.get_or_404(GrantApplication, application_id)
    
    application.comment = request.form.get('comment')
    db.session.commit()
    
    flash('Feedback submitted successfully!', 'success')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/account', methods=['GET', 'POST'])
def account():
    """
    User account page with password change and application history.
    
    Displays user information and application history, and handles
    password change requests.
    
    Returns:
        str: Rendered HTML template for account page or redirect if not logged in.
    """
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('main.login'))
    
    user = db.get_or_404(User, session['user_id'])
    
    password_form = PasswordChangeForm()
    
    if password_form.validate_on_submit():
        if check_password_hash(user.password, password_form.old_password.data):
            user.password = generate_password_hash(password_form.new_password.data)
            db.session.commit()
            flash('Your password has been updated successfully!', 'success')
            return redirect(url_for('main.account'))
        else:
            flash('Current password is incorrect.', 'danger')
    
    applications = db.session.execute(
        db.select(GrantApplication).filter_by(user_id=session['user_id']).order_by(GrantApplication.date_submitted.desc())
    ).scalars().all()
    
    return render_template('account.html', password_form=password_form, applications=applications)

news_cache = {
    'data': [],
    'last_updated': None
}

def fetch_gla_grant_news():
    """
    Fetch GLA grant news articles from Bing News - optimized.
    
    This function scrapes news related to GLA grants from Bing News
    search results and caches them to avoid excessive requests.
    
    Returns:
        list: List of article dictionaries with title, URL, source, date, and summary.
    """
    if news_cache['last_updated'] and datetime.now() - news_cache['last_updated'] < timedelta(hours=6):
        return news_cache['data']
    
    news_cache['is_fetching'] = True
    
    articles = []
    
    funding_programs = [
        "Greater London Authority grants",
        "London Community Energy Fund",
        "GLA funding programmes",
        "London grant funding",
        "Mayor of London funding"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for program in funding_programs[:3]:
        try:
            encoded_query = requests.utils.quote(program)
            bing_url = f"https://www.bing.com/news/search?q={encoded_query}"
            
            response = requests.get(bing_url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_cards = soup.select('.news-card')
            
            if not news_cards:
                news_cards = soup.select('.newsitem')
            
            if not news_cards:
                news_cards = soup.select('article')
                
            for card in news_cards[:7]:
                try:
                    title_element = (
                        card.select_one('a.title') or 
                        card.select_one('.title a') or 
                        card.select_one('h3 a') or
                        card.select_one('h2 a')
                    )
                    
                    if title_element:
                        title = title_element.text.strip()
                        url = title_element['href']
                        
                        if any(article['title'] == title for article in articles):
                            continue
                        
                        provider_element = (
                            card.select_one('.source a') or 
                            card.select_one('.provider') or
                            card.select_one('.source')
                        )
                        source = provider_element.text.strip() if provider_element else "News Source"
                        
                        date_element = (
                            card.select_one('.source span') or 
                            card.select_one('.datetime') or
                            card.select_one('time')
                        )
                        date = date_element.text.strip() if date_element else "Recent"
                        
                        summary_element = (
                            card.select_one('.snippet') or 
                            card.select_one('.abstract') or
                            card.select_one('p')
                        )
                        summary = summary_element.text.strip() if summary_element else ""
                        
                        articles.append({
                            'title': title,
                            'url': url,
                            'source': source,
                            'date': date,
                            'summary': summary
                        })
                except Exception as e:
                    print(f"Error parsing Bing news card for {program}: {e}")
                    continue
                
        except Exception as e:
            print(f"Error fetching from Bing News for {program}: {e}")
    
    unique_articles = []
    seen_titles = set()
    
    for article in articles:
        if article['title'] not in seen_titles and len(unique_articles) < 20:
            unique_articles.append(article)
            seen_titles.add(article['title'])
    
    news_cache['data'] = unique_articles
    news_cache['last_updated'] = datetime.now()
    news_cache['is_fetching'] = False
    
    return unique_articles

@main.route('/news')
def news():
    """
    News page route with pagination - accessible to all logged-in users.
    
    Displays news articles related to GLA grants with pagination.
    
    Returns:
        str: Rendered HTML template for news page or redirect if not logged in.
    """
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('main.login'))
    
    page = request.args.get('page', 1, type=int)
    
    if not news_cache.get('data') or (news_cache.get('last_updated') and 
                                    datetime.now() - news_cache['last_updated'] > timedelta(hours=6)):
        all_articles = fetch_gla_grant_news()
    else:
        all_articles = news_cache['data']
    
    all_articles = all_articles[:20]
    
    articles_per_page = 5
    total_pages = (len(all_articles) + articles_per_page - 1) // articles_per_page
    
    page = max(1, min(page, total_pages if total_pages > 0 else 1))
    
    start_idx = (page - 1) * articles_per_page
    end_idx = start_idx + articles_per_page
    page_articles = all_articles[start_idx:end_idx]
    
    return render_template('news.html', articles=all_articles, page_articles=page_articles,
                          current_page=page, total_pages=total_pages)

@main.route('/reset-applications')
def reset_applications():
    """
    Admin route to reset only the grant applications - preserves user accounts.
    
    Deletes all grant applications from the database while preserving user accounts.
    Accessible only to admin users.
    
    Returns:
        Response: Redirect to admin dashboard after reset.
    """
    if 'user_id' not in session or not session.get('is_admin', False):
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('main.index'))
        
    try:
        from coursework2.gla_grants_app import db
        from coursework2.gla_grants_app.models import GrantApplication
        
        deleted_count = db.session.query(GrantApplication).delete()
        db.session.commit()
        
        flash(f'Successfully reset applications database. Deleted {deleted_count} application(s).', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting applications: {str(e)}', 'danger')
    
    return redirect(url_for('main.admin_dashboard'))