from flask import render_template, request, redirect, url_for
from .models import db, GrantApplication

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        # Save submission to database
        pass
    return render_template('submit.html')

@app.route('/admin')
def admin():
    applications = GrantApplication.query.all()
    return render_template('admin.html', applications=applications)
