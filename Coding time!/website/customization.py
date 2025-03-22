#import flask modules for route handling and get and post requests
from flask import Blueprint, request, g, session, jsonify
#imports the database for data handling
from . import db
#import the user table to check for pre-existing users
from .models import Preferences
#used to handle user data depending on their action
from flask_login import login_required, current_user

#template to import the function to __init__.py
customization = Blueprint('customization', __name__)

#function to change user theme
@customization.route('/save_theme', methods=['POST'])
@login_required
def save_theme():
    #retrieves current user theme
    theme = request.form.get('theme')
    
    if theme not in ['light', 'dark']:
        return jsonify({'success': False, 'error': 'The selected theme is invalid!'})
    
    try:
        # Update the session with the chosen theme
        session['theme'] = theme
        # Fetch or create user preferences for saving the theme
        preferences = Preferences.query.filter_by(user_id=current_user.id).first()
        if not preferences:
            preferences = Preferences(user_id=current_user.id)
            db.session.add(preferences)
        # Commit changes to the database
        preferences.theme = theme
        db.session.commit()
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
    
    
