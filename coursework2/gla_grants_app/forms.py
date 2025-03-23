from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class LoginForm(FlaskForm):
    """Form for user login"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    """Form for user registration"""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

class PasswordChangeForm(FlaskForm):
    """Form for changing user password"""
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', 
                                  validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Change Password')

class ApplicationForm(FlaskForm):
    """Form for submitting grant applications"""
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description (max 500 words)', validators=[DataRequired(), Length(max=5000)])
    category = SelectField('Category', validators=[DataRequired()], 
                         choices=[
                             ('Arts & Culture', 'Arts & Culture'),
                             ('Business', 'Business'),
                             ('Community', 'Community'),
                             ('Education', 'Education'),
                             ('Environment', 'Environment'),
                             ('Health', 'Health'),
                             ('Housing', 'Housing'),
                             ('Youth Services', 'Youth Services')
                         ])
    question = TextAreaField('Question', validators=[DataRequired()])
    submit = SubmitField('Submit Application')