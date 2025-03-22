from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    db.init_app(app)

    with app.app_context():
        from app import routes  # Use absolute import

    return app

if __name__ == "__main__":
    from run import create_app, db

    app = create_app()
    with app.app_context():
        db.create_all()

    flask_app = create_app()
    flask_app.run(debug=True)