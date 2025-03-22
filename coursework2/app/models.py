from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class GrantApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    feedback = db.Column(db.Text)
