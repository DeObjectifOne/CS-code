#Blueprint imported so the function can be exported as a package
#request imported so data can be sent and retrieved upon user request
#g imported to make the theme variables global
#this is so they are applied to every webpage
#session imported to store the user's preferences during each login
#jsonify imported to transmit the user's preferences
#the data will go to other parts of the website
from flask import Blueprint, request, g, session, jsonify

#database imported for user-database interaction
from . import db

#Preferences table imported for user-table interaction
from .models import Preferences

#login_required imported to restrict usage of this function
#this means it cannot be used unless the user is logged in
#current_user imported for session purposes
#allows flask to detect certain users whenever they're using the website
from flask_login import login_required, current_user

#blueprint for the customization template
#can be used for importing purposes
customization = Blueprint('customization', __name__)

#theme function
#used to change the user's theme
#and to save the user's preferences
@customization.route('/save_theme', methods=['POST'])
@login_required
def save_theme():

    #the function begins by detecting the user's theme
    #the theme variable will then equal the user's theme of choice
    theme = request.form.get('theme')
    if theme in ['light', 'dark']:
        session['theme'] = theme
        #if the theme is already saved, flask will go into the database
        #it will then locate the Preferences table
        #it will scan the preference table for the theme variable
        #if its already set, the website retains their theme of choice
        #even after their previous session
        preferences = Preferences.query.filter_by(user_id=current_user.id).first()
        if not preferences:
            #if the column is empty
            #the new choice is added to the table insted
            preferences = Preferences(user_id=current_user.id, theme=theme)
            db.session.add(preferences)
        else:
            #the original theme can be retained
            #if there has been no usage of it
            preferences.theme = theme
        db.session.commit()

        #jsonifty notifies the user if the operation was successful
        return jsonify({'success': True})
    #otherwise, it returns an error
    return jsonify({'success': False}), 400
