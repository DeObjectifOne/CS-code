from . import db
from datetime import datetime
from flask_login import UserMixin
from sqlachemy.sql import func

#user table
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    #used as a primary identifier for finding items
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)
    preferences = db.relationship('Preferences', backref='preferences_user', lazy=True, uselist=False)

#task table
class Task(db.Model):
    __tablename__ = 'tasks'
    #used as a primary identifier for finding items
    id = db.Column(db.Integer, primary_key=True)
    details = db.Column(db.String(150), nullable=False)
    #uses the correct timezone to display the date of creation
    creation_date = db.Column(db.DateTime, default=datetime.utcnow())
    due_date = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.Integer, nullable=False)
    #variables used for task filtering
    completed = db.Column(db.Boolean, default=False)
    starred = db.Column(db.Boolean, default=False)
    #variable used to link all tasks back to the required user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Preferences(db.Model):

    __tablename__ = 'preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    weight_due_date = db.Column(db.Float, nullable=False, default=0.4)
    weight_duration = db.Column(db.Float, nullable=False, default=0.3)
    weight_priority = db.Column(db.Float, nullable=False, default=0.2)
    weight_difficulty = db.Column(db.Float, nullable=False, default=0.1)

    enable_due_date = db.Column(db.Boolean, default=True)
    enable_duration = db.Column(db.Boolean, default=True)
    enable_priority = db.Column(db.Boolean, default=True)
    enable_difficulty = db.Column(db.Boolean, default=True)
