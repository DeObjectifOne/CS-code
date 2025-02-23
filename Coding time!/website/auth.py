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

    # Prevent already authenticated users from logging in again
    if current_user.is_authenticated:
        flash('You are already logged in', 'info')
        return redirect(url_for('views.home'))

    # Initialize login_attempts in the session if it doesn't exist
    if 'login_attempts' not in session:
        session['login_attempts'] = 0

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Ensure all fields are completed
        if not email or not password:
            flash('All fields are required', 'danger')
            return render_template('login.html')

        # Check if user exists
        user = User.query.filter_by(email=email).first()

        # If user exists and password matches
        if user and check_password_hash(user.password, password):
            session['login_attempts'] = 0  # Reset attempts on successful login
            flash('Login successful', 'success')
            login_user(user, remember=True)
            return redirect(url_for('views.home'))

        # Increment login_attempts on failed login
        session['login_attempts'] += 1

        # Limit login attempts to prevent brute force attacks
        if session['login_attempts'] >= 5:
            flash('Too many failed attempts. Please reset your password.', 'danger')
            return redirect(url_for('auth.reset_password'))

        flash('Invalid email or password', 'danger')
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

#route for the user to reset their password
@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():

    #this block occurs if the user selects to change their password
    #can also occur if the user isn't able to login with their password 2x
    if request.method == 'POST':
        #the email also needs to be inputted
        #this is so the function can find the password associated with the email
        #and therefore proceed to change it
        email = request.form.get('email')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        #error message if the user does not complete all the required fields
        if not email or not new_password or not confirm_password:
            flash("All fields are required.", 'danger')
            return render_template('reset_password.html')

        #error message if the provided email isn't findable
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No account found with this email.", 'danger')
            return render_template('reset_password.html')

        #error message if the user's inputted passwords are not the same
        if new_password != confirm_password:
            flash("Passwords do not match.", 'danger')
            return render_template('reset_password.html')

        #if the user passes all these checks, the new password is inserted into the user table
        #the new password is hashed for security purposes'
        #it is then added to the slot of the original password
        user.password = generate_password_hash(new_password)
        db.session.commit()

        #the user is promptly informed of the successful operation
        flash("Password reset successful. Please log in.", 'danger')
        #they are redirected to the login page to try again
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html')

#route for changing account details in the app
@auth.route('/update-account', methods=['GET', 'POST'])
#the function works only in the app
#therefore the user has to be in-session
@login_required
def update_account():

    #POST method used to send requests to the database
    if request.method == 'POST':

        #the user is able to alter one of these attributes
        #by default, these variables are set to what the user inputted when they registered
        new_username = request.form.get('username')
        new_email = request.form.get('email')
        new_password = request.form.get('password')

        #the app checks the inputted email first to see if it is already in use by another user
        existing_user = User.query.filter_by(email=new_email).first()

        #if the email is in use but does not match the current user, an error message pops up
        if existing_user and existing_user.id != current_user.id:
            flash("An email like this already exists", category="error")
            return redirect(url_for('views.settings'))

        #once this checked is passed, the new details are then inserted into their database columns
        current_user.username = new_username
        current_user.email = new_email
        current_user.password = new_password

        #the new password is hashed after werkzeug security generates a new one
        #this if for security purposes so other users cannot directly see the new password
        if new_password:
            from werkzeug.security import generate_password_hash
            current_user.password = generate_password_hash(new_password)

        #the changes are then made to the database
        db.session.commit()

        #the user is then returned to the home page
        flash("Account updated successfully", category="success")
        return redirect(url_for('views.home'))

    return render_template('settings.html', user=current_user)

#route for deleting the user's account 
@auth.route('/delete-account', methods=['GET', 'POST'])
#can only occur when the user is in-session
#should be impossible when the user is logged out
@login_required
def delete_account():
    #POST method used
    #as the database needs to send a request to delete the user account
    if request.method == 'POST':

        #user id retrieved by using the current_user id
        #this is so the database knows what it is deleting
        user = User.query.get(current_user.id)

        #conditinal for if the user id is found or not found
        if user:

            #this branch occurs if the id has been found
            #the function deletes the data of each table one by one
            Task.query.filter_by(user_id=user.id).delete()
            Preferences.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            #the changes are then confirmed
            #so the table will now be empty of that user and their associated data
            db.session.commit()

            #a confirmation message is sent to assure the user that their account is gone
            #they are subsequently logged out and sent to the login page
            flash('Your account and all associated data have been successfully deleted.', category='success')
            return redirect(url_for('auth.login'))

        
        else:

            #branch for if the user could not be found
            #an error message is sent to say the account couldn't be located
            flash('Account not found.', category='error')
            return redirect(url_for('views.settings'))

    return redirect(url_for('views.settings'))
