#import flask modules for route handling and get and post requests
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
#imports the database for data handling
from . import db
#import the user table to check for pre-existing users
from .models import User, Task, Preferences
#used to handle user data depending on their action
from flask_login import login_user, login_required, logout_user, current_user
#used to make a WSGI (Web Server Gateway Interface) to handle user security
from werkzeug.security import check_password_hash, generate_password_hash

#blueprint for the auth template
auth = Blueprint('auth', __name__)

import re

#route for the login page
@auth.route('/login', methods=['GET', 'POST'])
def login():

    # Prevent already authenticated users from logging in again
    if current_user.is_authenticated:
        flash('You are already logged in', 'info')
        return redirect(url_for('views.home'))

    # Initialize login_attempts in the session if it doesn't exist
    if 'login_attempts' not in session:
        session['login_attempts'] = 0

    if request.method == "POST":
        username_or_email = request.form.get("username_or_email")
        password = request.form.get("password")

        # Ensure all fields are completed
        if not username_or_email or not password:
            flash('All fields are required', 'danger')
            return render_template('login.html')

        #Check if user exists via email
        if "@" in username_or_email:
            user = User.query.filter_by(email=username_or_email).first()
            if not user:
                flash('No user has been found with this email', 'danger')
                return render_template('login.html')
        #Otherwise, their password is checked
        else:
            user = User.query.filter_by(username=username_or_email).first()
            if not user:
                flash('No account has been found with this username', 'danger')
                return render_template('login.html')

        # If user exists and password matches
        if user and check_password_hash(user.password, password):
            # Reset attempts on successful login
            session['login_attempts'] = 0 
            flash('Login successful', 'success')
            login_user(user, remember=True)
            return redirect(url_for('views.home'))

        # Increment login_attempts on failed login
        session['login_attempts'] += 1

        # Limit login attempts to prevent brute force attacks or server overload
        if session['login_attempts'] >= 5:
            flash('Too many failed attempts. Please reset your password.', 'danger')
            return redirect(url_for('auth.reset_password'))

        flash('Invalid username/email or password', 'danger')
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
        flash('You are already logged in', 'info')
        return redirect(url_for('views.home'))

    #main registration function
    #retrieves user details
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        #function to make sure all fields are complete
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return redirect(url_for('auth.register'))
        
        #forces the user to not have special characters in their username
        if not username.isalnum():
            flash("Special characters cannot be included in your username, please try again!", "danger")
            return redirect(url_for("auth.register"))

        #dictionary to keep track of password issues
        password_errors = []

        #password required to be atleast 8 characters
        if len(password) < 8:
            password_errors.append("The password must be, at minimum, 8 characters long")

        #the password must also have atleast one number
        if not any(char.isdigit() for char in password):
            password_errors.append("The password must contain at least one number or more")

        #password must atleast contain one special character as listed below
        special_characters =  r'!@#$%^&*(),.?":{}|<>'
        if not any(char in special_characters for char in password):
            password_errors.append("The password must contain at least one special character")

        #if any of the errors are detected, the page will reload
        if password_errors:
            for error in password_errors:
                flash(error, 'danger')
            return redirect(url_for('auth.register'))

        #the user's details are checked to see if a duplicate email exists
        user = User.query.filter_by(email=email).first()

        if user:
            flash('A user with this email already exists', 'danger')
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
                flash('Registration successful', 'success')
                return redirect(url_for('views.home'))
            #function for if any errors occur during the process
            except Exception as e:
                db.session.rollback()
                flash('An error occured while trying you register you, please try again', 'danger')
                print(f"Error: {e}")

    return render_template('register.html', user=current_user)

#function to reset the user's password
@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():

    #the user's username or email is retrieved along with two instances of their new password
    #the username/email will be used to link the user's password back to the user
    if request.method == 'POST':
        username_or_email = request.form.get("username_or_email")
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        #forces the user to fill out all the fields
        if not username_or_email or not new_password or not confirm_password:
            flash("All fields are required.", 'danger')
            return render_template('reset_password.html')


        #checks if the provided email exists
        if "@" in username_or_email:
            user = User.query.filter_by(email=username_or_email).first()
            if not user:
                flash('No user has been found with this email', 'danger')
                return render_template('reset_password.html')
        #the same is done if the user's provided username does not exist
        else:
            user = User.query.filter_by(username=username_or_email).first()
            if not user:
                flash('No account has been found with this username', 'danger')
                return render_template('reset_password.html')

        #both instances of the new password have to match
        #common practice on similar websites
        if new_password != confirm_password:
            flash("Passwords do not match.", 'danger')
            return render_template('reset_password.html')
        
        #the new_passwords are checked to see if they meet the criteria
        password_errors = []

        #the new password has to be atleast 8 characters long
        if len(new_password) < 8:
            password_errors.append("The password must be, at minimum, 8 characters long")

        #the new password must also contain at least one number
        if not any(char.isdigit() for char in new_password):
            password_errors.append("The password must contain at least one number or more")

        #the new password must contain at least one special character
        special_characters =  r'!@#$%^&*(),.?":{}|<>'
        if not any(char in special_characters for char in new_password):
            password_errors.append("The password must contain at least one special character")

        #if any of the aforementioned errors are detected, the user is forced back to the login page
        if password_errors:
            for error in password_errors:
                flash(error, 'danger')
            return redirect(url_for('auth.reset_password'))       

        #the new password is accepted otherwise and hashed for extra security
        user.password = generate_password_hash(new_password)
        db.session.commit()

        #with the new password now in the database, the user can now login again
        flash("Password reset successful. Please log in.", 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html')

#function for updating the user's details within the website
@auth.route('/update-account', methods=['GET', 'POST'])
@login_required
def update_account():

    if request.method == 'POST':

        #the user's current details are assigned to the new vvariables
        #the user can likewise ignore this
        new_username = request.form.get('username')
        new_email = request.form.get('email')
        new_password = request.form.get('password')

        #the user has to fill out all the details if they want any changes
        #if they want to change one detail, they simply leave the other two details alone
        #they will be automatically filled with the original details
        if not new_username or not new_email or not new_password:
            flash('All fields are required', 'danger')
            return render_template('account.html')

        #if the user re-enters their email, they're told they are already using said email
        existing_user = User.query.filter_by(email=new_email).first()
        if existing_user and existing_user.id != current_user.id:
            flash("You are already using this email", 'danger')
            return redirect(url_for('views.settings'))

        #password dictionary to keep track of errors
        password_errors = []

        #the new password must be atleast 8 characters
        if len(new_password) < 8:
            password_errors.append("The password must be, at minimum, 8 characters long")

        #it must also contain atleast one number
        if not any(char.isdigit() for char in new_password):
            password_errors.append("The password must contain at least one number or more")

        #it must also contain at least one special character from the provided list
        special_characters =  r'!@#$%^&*(),.?":{}|<>'
        if not any(char in special_characters for char in new_password):
            password_errors.append("The password must contain at least one special character")

        #if any of these errors are added to the list, the user is forced to reload the page
        if password_errors:
            for error in password_errors:
                flash(error, 'danger')
            return redirect(url_for('auth.update_account'))
        
        #if the changes go through, the new details replace the original details
        current_user.username = new_username
        current_user.email = new_email
        if new_password:
            #the password is hashed (encrypted) for security purposes
            from werkzeug.security import generate_password_hash
            current_user.password = generate_password_hash(new_password)

        #changes are saved to the database
        db.session.commit()
        flash("Account updated successfully", 'success')
        return redirect(url_for('views.home'))

    return render_template('account.html', user=current_user)

#route for deleting a user account
@auth.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():

    if request.method == 'POST':

        #the user's current id is retrieved
        user = User.query.get(current_user.id)

        if user:
            #the user's task and preferences table are deleted
            Task.query.filter_by(user_id=user.id).delete()
            Preferences.query.filter_by(user_id=user.id).delete()
            #the user themselves are deleted
            db.session.delete(user)
            #changes are saved
            db.session.commit()
            #message sent to the user
            flash('Your account and all associated data have been successfully deleted. Thank you for using our website!', 'success')
            return redirect(url_for('auth.login'))
        else:
            #otherwise, the account is unable to be found and the function cancelled
            flash('Account not able to be located', 'danger')
            return redirect(url_for('views.settings'))

    return redirect(url_for('auth.login'))
