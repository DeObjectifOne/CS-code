from flask import Blueprint, render_template

#blueprint function
#combines all the routes into one package
#so they can be all exported together
views = Blueprint('views', __name__)

#route for the home page
@views.route('/')
def home():
    return render_template('home.html')

#route for the settings page
@views.route('/settings')
def settings():
    return render_template('settings.html')
