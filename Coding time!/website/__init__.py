from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import secrets
import os

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(24)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    # Import and register blueprint
    from .views import views
    app.register_blueprint(views)

    # Import models so tables can be created
    from .models import User, Task
    with app.app_context():
        db.create_all()

    return app
