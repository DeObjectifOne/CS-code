from flask import Flask
import os

def create_app():

    #imports all files in templates directly to config.py to be rendered
    template_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'frontend', 'templates')
    app = Flask(__name__, template_folder=template_dir)
    app.config['SECRET_KEY'] = 'f0efh10f'

    #imports all routes from views
    #makes them run when the app is run
    from .views import views
    app.register_blueprint(views)

    return app
