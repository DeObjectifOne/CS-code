from flask import Blueprint, render_template

views = Blueprint('views', __name__)

#route for the home page
@views.route('/')
def home():
    return render_template('home.html')

#route for the settings page
@views.route('/settings')
def settings():
    return render_template('settings.html')

#route for the login page
@views.route('/login')
def login():
    return render_template('login.html')

#route for the register page
@views.route('/register')
def register():
    return render_template('register.html')
