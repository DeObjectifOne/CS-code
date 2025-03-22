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
    
    #establishes the website whenever run
    app = Flask(__name__)
    #secret key established to be used for in-app security
    app.secret_key = secrets.token_hex(24)
    #establishes the database each time the session begins, even if there is none
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    # Import and register blueprints
    from .auth import auth
    from .views import views
    from .utils import utils
    from .sort import sort
    from .customization import customization

    #adds an identifier so they can be easily registerded
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
    
    #makes the user available across all Jinja templates
    #makes it so the user does not need manual importing into all templates
    @app.context_processor
    def inject_user():
        return {
            'user': current_user,
            'current_page' : {
                'views.home': 'Home',
                'utils.create_task': 'Add Task',
                'views.settings': 'Settings',
                'auth.logout': 'Logout',
                'auth.login': 'Login',
                'auth.register': 'Register',
            }.get(request.endpoint, 'Unknown Page')
        }
    
    #Makes sure the user can only go to certain webpages when logged out
    @app.before_request
    def logout_state():
        if not current_user.is_authenticated and request.endpoint not in ['auth.login', 'auth.register', 'auth.reset_password']:
            return redirect(url_for('auth.login')) 

    #makes sure to set the theme to the user's default each time a new session is run
    @app.before_request
    def set_theme():
        if current_user.is_authenticated:
            preferences = Preferences.query.filter_by(user_id=current_user.id).first()
            g.theme = preferences.theme if preferences else 'light'
        else:
            g.theme = session.get('theme', 'light') 

    #formats date time variables universally for ease of import
    @app.template_filter('datetimeformat')
    def date_formatting(value):
            return value.strftime('%Y-%m-%dT%H:%M') if value else ''

    return app
