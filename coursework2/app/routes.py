from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from . import db
from .models import User, GrantApplication, Grant
from .forms import LoginForm, RegistrationForm, GrantApplicationForm, FeedbackForm
import pandas as pd
import plotly
import plotly.express as px
import json
from functools import wraps

main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Custom decorator for admin access
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# Main routes
@main_bp.route('/')
def index():
    # Create a simple visualization for the homepage
    grants = Grant.query.all()
    if grants:
        df = pd.DataFrame([(g.theme, g.amount) for g in grants], columns=['Theme', 'Amount'])
        df_grouped = df.groupby('Theme').sum().reset_index()
        fig = px.bar(df_grouped, x='Theme', y='Amount', title='Grant Distribution by Theme')
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        graph_json = None
    
    return render_template('index.html', graph_json=graph_json)

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=form)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    
    return render_template('login.html', form=form)

@main_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main_bp.route('/dashboard')
def dashboard():
    # Create visualizations for trends analysis
    grants = Grant.query.all()
    if not grants:
        flash('No grant data available.', 'warning')
        return render_template('dashboard.html')
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame([
        {
            'Year': g.financial_year,
            'Theme': g.theme,
            'Programme': g.programme_name,
            'Amount': g.amount
        } for g in grants
    ])
    
    # Create multiple visualizations
    fig1 = px.bar(df.groupby('Theme').sum().reset_index(), 
                 x='Theme', y='Amount', title='Total Grant Amount by Theme')
    
    fig2 = px.line(df.groupby('Year').sum().reset_index(),
                  x='Year', y='Amount', title='Grant Trends Over Years')
    
    fig3 = px.pie(df, values='Amount', names='Programme', title='Grant Distribution by Programme')
    
    graphs = {
        'graph1': json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder),
        'graph2': json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder),
        'graph3': json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder)
    }
    
    return render_template('dashboard.html', graphs=graphs)

@main_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    form = GrantApplicationForm()
    if form.validate_on_submit():
        application = GrantApplication(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            question=form.question.data,
            author=current_user
        )
        db.session.add(application)
        db.session.commit()
        flash('Your application has been submitted successfully!', 'success')
        return redirect(url_for('main.my_applications'))
    
    return render_template('submit.html', form=form)

@main_bp.route('/my_applications')
@login_required
def my_applications():
    applications = GrantApplication.query.filter_by(user_id=current_user.id).all()
    return render_template('my_applications.html', applications=applications)

@main_bp.route('/application/<int:id>')
@login_required
def view_application(id):
    application = GrantApplication.query.get_or_404(id)
    if application.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to view this application.', 'danger')
        return redirect(url_for('main.my_applications'))
    
    return render_template('view_application.html', application=application)

# Admin routes
@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    applications = GrantApplication.query.all()
    return render_template('admin/dashboard.html', applications=applications)

@admin_bp.route('/application/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def review_application(id):
    application = GrantApplication.query.get_or_404(id)
    form = FeedbackForm()
    
    if form.validate_on_submit():
        application.feedback = form.feedback.data
        application.status = form.status.data
        db.session.commit()
        flash('Feedback submitted successfully.', 'success')
        return redirect(url_for('admin.admin_dashboard'))
    
    if application.feedback:
        form.feedback.data = application.feedback
        form.status.data = application.status
    
    return render_template('admin/review.html', application=application, form=form)

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# API Routes for grant data
@main_bp.route('/api/grants')
def get_grants():
    grants = Grant.query.all()
    grant_data = [{
        'id': g.id,
        'financial_year': g.financial_year,
        'organisation': g.organisation,
        'project_name': g.project_name,
        'programme_name': g.programme_name,
        'theme': g.theme,
        'amount': g.amount
    } for g in grants]
    
    return jsonify(grant_data)

@main_bp.route('/api/grants/<theme>')
def get_grants_by_theme(theme):
    grants = Grant.query.filter_by(theme=theme).all()
    grant_data = [{
        'id': g.id,
        'financial_year': g.financial_year,
        'organisation': g.organisation,
        'project_name': g.project_name,
        'programme_name': g.programme_name,
        'theme': g.theme,
        'amount': g.amount
    } for g in grants]
    
    return jsonify(grant_data)