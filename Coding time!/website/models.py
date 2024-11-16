from . import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    details = db.Column(db.String(150), nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)  # Changed to DateTime for proper dates
    duration = db.Column(db.Integer, nullable=False)
    priority = db.Column(db.String(50), nullable=False)  # Added max length for clarity
    difficulty = db.Column(db.String(50), nullable=False)  # Added max length for clarity
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Corrected ForeignKey
