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

    #changes the function name
    #makes it shorter to type out
    app = Flask(__name__)
    #used for website encryption
    #added layer of security
    app.secret_key = secrets.token_hex(24)
    #the database is set to run once the website runs
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    # Import and register blueprints
    #this is so they're run when the website runs
    from .auth import auth
    from .views import views
    from .utils import utils
    from .sort import sort

    #makes the url link for these blueprints valid
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(utils, url_prefix='/')
    app.register_blueprint(sort, url_prefix='/')

    #used to redirect users to the necessary pages upon booting up the website
    login_manager = LoginManager()
    login_manager.login_view = 'views.login'
    login_manager.init_app(app)

    # Import models so tables can be created
    from .models import User, Task
    with app.app_context():
        db.create_all()

    #used to return the user's details by using their id
    #this also works for linking the user to their tasks
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    #used to insert any of the dictionaries the user requires
    @app.context_processor
    def inject_user():
        return dict(user=current_user)

    #used to make sure that any datetime objects are formatted correctly
    #this allows for better display and editing of the task
    @app.template_filter('datetimeformat')
    def datetimeformat(value):
        if value:
            return value.strftime('%Y-%m-%dT%H:%M')
        return ''
    
    return app
