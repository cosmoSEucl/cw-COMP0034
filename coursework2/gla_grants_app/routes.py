from flask import Blueprint, render_template, redirect, url_for, request, flash
from gla_grants_app import db
from gla_grants_app.models import Grant, User, GrantApplication
from gla_grants_app.forms import ApplicationForm, LoginForm
from sqlalchemy import func
import plotly.express as px
import pandas as pd

# Create blueprint
main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

@main.route('/data-visualization')
def data_visualization():
    """Data visualization page route"""
    # Query the database to get grant data
    query = db.select(Grant.category, func.sum(Grant.amount_awarded).label('total_amount')).\
        group_by(Grant.category)
    result = db.session.execute(query).all()
    
    # Create dataframe for visualization
    df = pd.DataFrame([(r.category, r.total_amount) for r in result], 
                      columns=['Category', 'Total Amount'])
    
    # Create bar chart
    fig = px.bar(df, x='Category', y='Total Amount', 
                 title='Total Grant Amount by Category')
    
    # Convert chart to HTML
    chart_html = fig.to_html(full_html=False)
    
    return render_template('data_visualization.html', chart_html=chart_html)

@main.route('/grants-dataset')
def grants_dataset():
    """Grant dataset browsing page route"""
    # Get grants data from database
    grants = db.session.execute(db.select(Grant)).scalars().all()
    return render_template('grants_dataset.html', grants=grants)

@main.route('/submit-application', methods=['GET', 'POST'])
def submit_application():
    """Submit application page route"""
    form = ApplicationForm()
    
    if form.validate_on_submit():
        # Create new application from form data
        application = GrantApplication(
            user_id=1,  # Hardcoded for now, would normally use current_user.id
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
    # Get submitted applications from database
    applications = db.session.execute(db.select(GrantApplication)).scalars().all()
    return render_template('admin_dashboard.html', applications=applications)

@main.route('/admin-review/<int:application_id>', methods=['POST'])
def admin_review(application_id):
    """Admin review submission route"""
    # Get application
    application = db.get_or_404(GrantApplication, application_id)
    
    # Update comment
    application.comment = request.form.get('comment')
    db.session.commit()
    
    flash('Feedback submitted successfully!', 'success')
    return redirect(url_for('main.admin_dashboard'))