from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email

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

class LoginForm(FlaskForm):
    """Form for user login"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')