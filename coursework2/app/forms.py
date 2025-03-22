from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class GrantApplicationForm(FlaskForm):
    title = StringField("Grant Title", validators=[DataRequired()])
    description = TextAreaField("Project Description", validators=[DataRequired()])
    category = StringField("Category")
    submit = SubmitField("Submit Application")
