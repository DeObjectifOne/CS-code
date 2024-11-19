#import flask modules for route handling and get and post requests
from flask import Blueprint, render_template, request, flash, redirect, url_for

#imports the database for data handling
from . import db

#import the user table to check for pre-existing users
from .models import User

#used to handle user data depending on their action
from flask_login import login_user, login_required, logout_user, current_user

#used to make a WSGI (Web Server Gateway Interface) to handle user security
from werkzeug.security import check_password_hash, generate_password_hash

#blueprint for the views template
views = Blueprint('views', __name__)

#route for the home page
@views.route('/home')
@login_required
def home():
    
    from .models import Task, User
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('home.html', user=current_user, tasks=tasks)

#route for the settings page
@views.route('/settings')
def settings():
    return render_template('settings.html')

#route for the login page
@views.route('/login')
def login():
    
    #function that prevents the user from logging in again
    #detects this by seeing if the user is authenticated
    if current_user.is_authenticated:
        flash('You are already logged in', category='info')
        return redirect(url_for('views.home'))

    #makes the user submit their email and password
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        #function to make sure all fields are complete
        if not email or not password:
            flash('All fields are required', category='error')
            return render_template('login.html')

        #the user is then checked to see if they exist
        user = User.query.filter_by(email=email).first()

        #the user is then logged in if the user exists
        #and if the password hashed equals the hashed password
        if user and check_password_hash(user.password, password):
            flash('Login successful', category='success')
            login_user(user, remember=True)
            return redirect(url_for('views.home'))
        else:
            #otherwise, the user is denied entry
            flash('Invalid email or password', category='error')
            return render_template('login.html')

    return render_template('login.html')

#logout function
@views.route('/logout')
@login_required
def logout():
    
    #function that erases user session data
    logout_user()
    return redirect(url_for('views.login'))

#route for the register page
@views.route('/register')
def register():

    #function that prevents the user from registering
    #detects this by seeing if the user is authenticated
    if current_user.is_authenticated:
        flash('You are already logged in', category='info')
        return redirect(url_for('views.home'))

    #main registration function
    #retrieves user details
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        #function to make sure all fields are complete
        if not username or not email or not password:
            flash('All fields are required', category='error')
            return redirect(url_for('views.register'))

        #the user's details are checked to see if a duplicate email exists
        user = User.query.filter_by(email=email).first()

        if user:
            flash('A user with this email already exists', category='error')
            return redirect(url_for('views.login'))
        else:
            try:
                #the user is created as a variable with 3 attributes
                new_user = User(
                    username=username, 
                    email=email, 
                    #the password is hashed for increased security
                    password=generate_password_hash(password, method='pbkdf2:sha256')
                )
                #the user is then added to the database
                db.session.add(new_user)
                db.session.commit()
                #the application then remebers the user's login
                login_user(new_user, remember=True)
                flash('Registration successful')
                return redirect(url_for('views.home'))
            #function for if any errors occur during the process
            except Exception as e:
                db.session.rollback()
                flash('An error occured while trying you register you, please try again')
                print(f"Error: {e}")


    return render_template('register.html', user=current_user)

#Creates a method that lets the user add tasks to their database
@views.route('/creation', methods=['GET', 'POST'])
@login_required
def create_task():

    try:
        
        #retrieves the data from creation.html 
        if request.method == 'POST':
            details = request.form.get("details")
            duration = request.form.get("duration")
            due_date_str = request.form.get("due_date")
            priority = request.form.get("priority")
            difficulty = request.form.get("difficulty")

            #used to convert the due_date into a datetime variable
            #this is so it can be displayed on the main page
            due_date = datetime.fromisoformat(due_date_str)

            #checks if the data has been imported
            if not details:
                flash("Task details are required", category='error')
            else:
                
                #all the data is imported to the database
                from .models import Task
                new_task = Task(
                    details=details,
                    duration=duration,
                    due_date=due_date,
                    priority=priority,
                    difficulty=difficulty,
                    user_id=current_user.id
                )
                #the changes are commited
                #the user then returns to the home page
                db.session.add(new_task)
                db.session.commit() 
                flash("Task created successfully", category='success')
                return redirect(url_for('views.home'))
    
    #an error is displayed if the data could not be imported
    except ValueError:
        flash("Invalid input, try again", category="error")
        return redirect(url_for('create_task'))

    return render_template('creation.html', user=current_user)
