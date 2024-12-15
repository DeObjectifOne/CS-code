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

    theme = request.form.get('theme')
    
    if theme not in ['light', 'dark']:
        return jsonify({'success': False, 'error': 'Invalid theme'}), 400
    
    try:
        # Update the session with the chosen theme
        session['theme'] = theme

        # Fetch or create user preferences for saving the theme
        preferences = Preferences.query.filter_by(user_id=current_user.id).first()
        if not preferences:
            preferences = Preferences(user_id=current_user.id, theme=theme)
            db.session.add(preferences)
        else:
            preferences.theme = theme

        # Commit changes to the database
        db.session.commit()

        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
