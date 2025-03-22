from flask import render_template, request, redirect, url_for
from run import db  # Import the db instance from run.py
from .models import GrantApplication
from .forms import GrantApplicationForm
from . import create_app

app = create_app()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    form = GrantApplicationForm()
    if form.validate_on_submit():
        new_application = GrantApplication(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data
        )
        db.session.add(new_application)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('submit.html', form=form)

@app.route('/admin')
def admin():
    applications = GrantApplication.query.all()
    return render_template('admin.html', applications=applications)