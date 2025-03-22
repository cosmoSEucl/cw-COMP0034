from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from .models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose another one.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use another one.')

class GrantApplicationForm(FlaskForm):
    title = StringField('Application Title', validators=[DataRequired(), Length(max=255)])
    category = SelectField('Category', 
                         choices=[('Youth Services', 'Youth Services'), 
                                  ('Housing', 'Housing'), 
                                  ('Environment', 'Environment'),
                                  ('Culture', 'Culture'),
                                  ('Education', 'Education'),
                                  ('Other', 'Other')], 
                         validators=[DataRequired()])
    description = TextAreaField('Project Description', validators=[DataRequired()])
    question = TextAreaField('Specific Questions or Concerns')
    submit = SubmitField('Submit Application')

class FeedbackForm(FlaskForm):
    feedback = TextAreaField('Feedback', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Under Review', 'Under Review'),
        ('Feedback Provided', 'Feedback Provided'),
        ('Rejected', 'Rejected'),
        ('Approved', 'Approved')
    ])
    submit = SubmitField('Submit Feedback')