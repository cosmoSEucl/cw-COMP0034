from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from coursework2.gla_grants_app import db
from coursework2.gla_grants_app.models import Grant, User, GrantApplication
from coursework2.gla_grants_app.forms import ApplicationForm, LoginForm, RegistrationForm, PasswordChangeForm
from sqlalchemy import func
import plotly.express as px
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

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
    """Route to display Dash app within Flask template"""
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('main.login'))
        
    # Render the template with the iframe that embeds the Dash app
    return render_template('dash_visualization.html')

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

@main.route('/account', methods=['GET', 'POST'])
def account():
    """User account page with password change and application history"""
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('main.login'))
    
    # Get the current user
    user = db.get_or_404(User, session['user_id'])
    
    # Initialize the password change form
    password_form = PasswordChangeForm()
    
    # Handle form submission for password change
    if password_form.validate_on_submit():
        # Verify old password
        if check_password_hash(user.password, password_form.old_password.data):
            # Update with new hashed password
            user.password = generate_password_hash(password_form.new_password.data)
            db.session.commit()
            flash('Your password has been updated successfully!', 'success')
            return redirect(url_for('main.account'))
        else:
            flash('Current password is incorrect.', 'danger')
    
    # Get user's application history
    applications = db.session.execute(
        db.select(GrantApplication).filter_by(user_id=session['user_id']).order_by(GrantApplication.date_submitted.desc())
    ).scalars().all()
    
    return render_template('account.html', password_form=password_form, applications=applications)

# News cache to avoid excessive requests
news_cache = {
    'data': [],
    'last_updated': None
}

# Modified function to limit articles and reduce loading time
def fetch_gla_grant_news():
    """Fetch GLA grant news articles from Bing News - optimized"""
    # Check cache first (refresh every 6 hours)
    if news_cache['last_updated'] and datetime.now() - news_cache['last_updated'] < timedelta(hours=6):
        return news_cache['data']
    
    # Set fetching flag
    news_cache['is_fetching'] = True
    
    articles = []
    
    # Funding programs to search for
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
    
    # Search for each program
    for program in funding_programs[:3]:  # Limit to 3 searches for performance
        try:
            # URL encode the search query
            encoded_query = requests.utils.quote(program)
            bing_url = f"https://www.bing.com/news/search?q={encoded_query}"
            
            response = requests.get(bing_url, headers=headers, timeout=5)  # Add timeout
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find news cards
            news_cards = soup.select('.news-card')
            
            # If no results with this selector, try alternative selectors
            if not news_cards:
                news_cards = soup.select('.newsitem')
            
            if not news_cards:
                news_cards = soup.select('article')
                
            for card in news_cards[:7]:  # Get up to 7 articles from each search
                try:
                    # Try different selectors for title elements
                    title_element = (
                        card.select_one('a.title') or 
                        card.select_one('.title a') or 
                        card.select_one('h3 a') or
                        card.select_one('h2 a')
                    )
                    
                    if title_element:
                        title = title_element.text.strip()
                        url = title_element['href']
                        
                        # Skip duplicates
                        if any(article['title'] == title for article in articles):
                            continue
                        
                        # Extract source and date
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
                        
                        # Extract summary
                        summary_element = (
                            card.select_one('.snippet') or 
                            card.select_one('.abstract') or
                            card.select_one('p')
                        )
                        summary = summary_element.text.strip() if summary_element else ""
                        
                        # Add to articles list
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
    
    # Deduplicate and limit to 20 articles
    unique_articles = []
    seen_titles = set()
    
    for article in articles:
        if article['title'] not in seen_titles and len(unique_articles) < 20:
            unique_articles.append(article)
            seen_titles.add(article['title'])
    
    # Update cache with collected articles
    news_cache['data'] = unique_articles
    news_cache['last_updated'] = datetime.now()
    news_cache['is_fetching'] = False  # Reset fetching flag
    
    return unique_articles

@main.route('/news')
def news():
    """News page route with pagination - accessible to all logged-in users"""
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('main.login'))
    
    # Get page number from query parameters, default to page 1
    page = request.args.get('page', 1, type=int)
    
    # Fetch news if cache is empty or expired
    if not news_cache.get('data') or (news_cache.get('last_updated') and 
                                    datetime.now() - news_cache['last_updated'] > timedelta(hours=6)):
        all_articles = fetch_gla_grant_news()
    else:
        all_articles = news_cache['data']
    
    # Limit to 20 articles maximum
    all_articles = all_articles[:20]
    
    # Calculate pagination
    articles_per_page = 5
    total_pages = (len(all_articles) + articles_per_page - 1) // articles_per_page
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages if total_pages > 0 else 1))
    
    # Get articles for the current page
    start_idx = (page - 1) * articles_per_page
    end_idx = start_idx + articles_per_page
    page_articles = all_articles[start_idx:end_idx]
    
    return render_template('news.html', articles=all_articles, page_articles=page_articles,
                          current_page=page, total_pages=total_pages)

@main.route('/reset-applications')
def reset_applications():
    """Admin route to reset only the grant applications - preserves user accounts"""
    if 'user_id' not in session or not session.get('is_admin', False):
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('main.index'))
        
    try:
        # Import needed modules
        from coursework2.gla_grants_app import db
        from coursework2.gla_grants_app.models import GrantApplication
        
        # Delete only the grant applications
        deleted_count = db.session.query(GrantApplication).delete()
        db.session.commit()
        
        flash(f'Successfully reset applications database. Deleted {deleted_count} application(s).', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting applications: {str(e)}', 'danger')
    
    return redirect(url_for('main.admin_dashboard'))