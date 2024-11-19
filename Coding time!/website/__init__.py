#used to import and support many web functions
from flask import Flask

#used for databases and CRUD operations
from flask_sqlalchemy import SQLAlchemy

#used to create a secret key
import secrets

#used to create direct/absolute paths to routes
import os

#used for handling user login queries and requests
from flask_login import LoginManager

#imports and creates the database in models.py
db = SQLAlchemy()
DB_NAME = "database.db"

#app function that instantiates all connected roots
def create_app():
    
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(24)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    # Import and register blueprint
    from .views import views
    app.register_blueprint(views)

    #used to redirect users to the necessary pages upon booting up the website
    login_manager = LoginManager()
    login_manager.login_view = 'views.login'
    login_manager.init_app(app)

    # Import models so tables can be created
    from .models import User, Task
    with app.app_context():
        db.create_all()

    #used to return the user's details by using their id
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    @app.context_processor
    def inject_user():
        return dict(user=current_user)
    
    return app
