from flask import Flask

from flask_sqlalchemy import SQLAlchemy

import secrets

import os

from flask_login import LoginManager

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

    login_manager = LoginManager()
    login_manager.login_view = 'views.login'
    login_manager.init_app(app)

    # Import models so tables can be created
    from .models import User, Task
    with app.app_context():
        db.create_all()

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    
    return app
