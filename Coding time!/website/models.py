#imports the database so it can be rendered
from . import db
#imports datetime objectd (specifically for dated variables)
from datetime import datetime
#UserMixin is able to call up the user properties
#this is used for things like authentication
from flask_login import UserMixin

#user table
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    #used as a primary identifier for finding items
    id = db.Column(db.Integer, primary_key=True)
    #user details for authentication
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    #variable used to link the user's tasks to the user account
    tasks = db.relationship('Task', backref='user', lazy=True)
    #variable used to link the user's preferences to the user account
    preferences = db.relationship('Preferences', backref='preferences_user', lazy=True, uselist=False)

#task table
class Task(db.Model):
    __tablename__ = 'tasks'
    #used as a primary identifier for finding items
    id = db.Column(db.Integer, primary_key=True)
    #stores the task details for searching
    details = db.Column(db.String(150), nullable=False)
    #stores the rest of the task attributes
    due_date = db.Column(db.DateTime, nullable=True)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow())
    duration = db.Column(db.Integer, nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    #variables used for task filtering
    completed = db.Column(db.Boolean, default=False)
    starred = db.Column(db.Boolean, default=False)
    #position value so the database knows where the task is in the list
    position = db.Column(db.Integer, default=0)
    #variable used to link all tasks back to the required user
    #a ForeignKey is used so the Task class is directly linked back to the User class
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

#user preferences table
class Preferences(db.Model):
    __tablename__ = 'preferences'
    #id used as a primary identifier to find variables
    id = db.Column(db.Integer, primary_key=True)
    #stores the saved weights of 4 variables
    #these variables are used so the user can automatically sort their tasks
    due_date_weight = db.Column(db.Float, nullable=False, default=0.25)
    duration_weight = db.Column(db.Float, nullable=False, default=0.25)
    priority_weight = db.Column(db.Float, nullable=False, default=0.25)
    difficulty_weight = db.Column(db.Float, nullable=False, default=0.25)
    #variable used to link all the user's preferences back to the required user
    #a ForeignKey is used so the Preferences class is directly linked back to the User class
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    #variable to save the user's theme for either light or dark mode
    theme = db.Column(db.String(10), default='light')
