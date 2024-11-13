from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from website.models.models import db, User, Task
import os
from os import path
from os.path import abspath, join, dirname


db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():

    #imports all files in templates directly to config.py to be rendered
    template_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'frontend', 'templates')
    app = Flask(__name__, template_folder=template_dir)
    
    app.config['SECRET_KEY'] = 'f0efh10f'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    
    #imports all routes from views
    #makes them run when the app is run
    from .views import views
    app.register_blueprint(views)

    with app.app_context():
        db.create_all()
    
    return app
