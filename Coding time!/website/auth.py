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

#blueprint for the auth template
auth = Blueprint('auth', __name__)

#route for the login page
@auth.route('/login', methods=['GET', 'POST'])
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
@auth.route('/logout')
@login_required
def logout():

    #function that erases user session data
    logout_user()
    return redirect(url_for('auth.login'))

#route for the register page
@auth.route('/register', methods=['GET', 'POST'])
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
            return redirect(url_for('auth.register'))

        #the user's details are checked to see if a duplicate email exists
        user = User.query.filter_by(email=email).first()

        if user:
            flash('A user with this email already exists', category='error')
            return redirect(url_for('auth.login'))
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

@auth.route('/update-account', methods=['GET', 'POST'])
@login_required
def update_account():

    if request.method == 'POST':

        new_username = request.form.get('username')
        new_email = request.form.get('email')
        new_password = request.form.get('password')

        existing_user = User.query.filter_by(email=new_email).first()

        if existing_user and existing_user.id != current_user.id:
            flash("You are already using this email", category="error")
            return redirect(url_for('views.settings'))

        current_user.username = new_username
        current_user.email = new_email
        current_user.password = new_password

        if new_password:

            from werkzeug.security import generate_password_hash
            current_user.password = generate_password_hash(new_password)

        db.session.commit()

        flash("Account updated successfully", category="success")
        return redirect(url_for('views.home'))

    return render_template('settings.html', user=current_user)

@auth.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':

        user = User.query.get(current_user.id)

        if user:

            Task.query.filter_by(user_id=user.id).delete()
            Preferences.query.filter_by(user_id=user.id).delete()

            db.session.delete(user)
            db.session.commit()

            flash('Your account and all associated data have been successfully deleted.', category='success')
            return redirect(url_for('auth.login'))

        
        else:

            flash('Account not found.', category='error')
            return redirect(url_for('views.settings'))

    return redirect(url_for('views.settings'))
