#import flask modules for route handling and get and post requests
from flask import Blueprint, request, g, session, jsonify

#imports the database for data handling
from . import db

#import the user table to check for pre-existing users
from .models import Preferences

#used to handle user data depending on their action
from flask_login import login_required, current_user

#blueprint for the auth template
customization = Blueprint('customization', __name__)

@customization.route('/save_theme', methods=['POST'])
@login_required
def save_theme():
    theme = request.form.get('theme')
    if theme in ['light', 'dark']:

        session['theme'] = theme

        preferences = Preferences.query.filter_by(user_id=current_user.id).first()
        if not preferences:

            preferences = Preferences(user_id=current_user.id, theme=theme)
            db.session.add(preferences)
        else:

            preferences.theme = theme
        
        db.session.commit()

        return jsonify({'success': True})

    return jsonify({'success': False}), 400