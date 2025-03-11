#used to import and support many web functions
from flask import Flask, g, session, request, redirect, url_for
#used for databases and CRUD operations
from flask_sqlalchemy import SQLAlchemy
#used to create a secret key
import secrets
#used to create direct/absolute paths to routes
import os
#used for handling user login queries and requests
from flask_login import LoginManager, current_user

#imports and creates the database in models.py
db = SQLAlchemy()
DB_NAME = "database.db"

#app function that instantiates all connected roots
def create_app():
    
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(24)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    # Import and register blueprints
    from .auth import auth
    from .views import views
    from .utils import utils
    from .sort import sort
    from .customization import customization

    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(utils, url_prefix='/')
    app.register_blueprint(sort, url_prefix='/')
    app.register_blueprint(customization, url_prefix='/')

    #used to redirect users to the necessary pages upon booting up the website
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # Import models so tables can be created
    from .models import User, Task, Preferences
    with app.app_context():
        db.create_all()

    #used to return the user's details by using their id
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    @app.context_processor
    def inject_user():
        return {'user': current_user}
    
    @app.context_processor
    def inject_current_page():
        
        page_names = {
            'views.home': 'Home',
            'utils.create_task': 'Add Task',
            'views.settings': 'Settings',
            'auth.logout': 'Logout',
            'auth.login': 'Login',
            'auth.register': 'Register',
        }

        current_page = page_names.get(request.endpoint, 'Unknown Page')
        return {'current_page': current_page}
    
    @app.before_request
    def redirect_if_not_logged_in():
        if not current_user.is_authenticated:
            if request.endpoint not in ['auth.login', 'auth.register', 'auth.reset_password']:
                return redirect(url_for('auth.login')) 

    @app.before_request
    def apply_user_theme():
        if current_user.is_authenticated:
            preferences = Preferences.query.filter_by(user_id=current_user.id).first()
            g.theme = preferences.theme if preferences and preferences.theme else 'light'
        else:
            g.theme = session.get('theme', 'light') 

    #makes it so the due_date variable from models.py is modelled uniformally
    #as a datetime function so it is always displayed the same
    @app.template_filter('datetimeformat')
    def datetimeformat(value):
        if value:
            return value.strftime('%Y-%m-%dT%H:%M')
        return ''

    return app
