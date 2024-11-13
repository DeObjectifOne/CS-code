from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=False, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), unique=True, nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    details = db.Column(db.String(150), nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.Integer, nullable=True)
    duration = db.Column(db.Integer, nullable=False)
    priority = db.Column(db.String, nullable=False)
    difficulty = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user_id'), nullable=False)
