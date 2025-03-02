#import flask modules for route handling and get and post requests
from flask import Blueprint, render_template, request, flash, redirect, url_for

#imports the database for data handling
from . import db

#import the task table to import data from it
from .models import Task

#used to handle user data depending on their action
from flask_login import login_required, current_user

#special import for the due_date function specifically
from datetime import datetime

#blueprint for the views template
views = Blueprint('views', __name__)

#route for the home page
@views.route('/home', methods=['GET', 'POST'])
@login_required
def home():

    #search query is empty for user entry
    search_query = ""

    if request.method == 'POST':
        search_query = request.form.get('search', "").strip

        #tasks are filtered for specific characters
        tasks = Task.query.filter(
            #confirmation to ask if task id matches the user's current id
            Task.user_id == current_user.id,
            #uses the ilike function to filter out words specifically
            Task.details.ilike(f"%{search_query}%")
        ).all()
    else:
        #displays all the user's tasks regardless of the search function
        tasks= Task.query.filter_by(user_id=current_user.id).all()

    user_preferences = Preferences.query.filter_by(id=current_user.id).first()
    if user_preferences:
        tasks = calculate_task_scores(tasks, user_preferences)

    priority_map = {1: "High", 2: "Medium", 3: "Low"}
    difficulty_map = {1: "Easy", 2: "Medium", 3: "Hard"}

    for task in tasks:
        task.priority_str = priority_map.get(task.priority, "Low")
        task.difficulty_str = difficulty_map.get(task.difficulty, "Easy")
    
    #the filtered function for tasks_due_today is returned to the user
    today = datetime.utcnow().date()
    tasks_due_today = [task for task in tasks if task.due_date and task.due_date.date() == today]
    #the filtered function for completed_tasks is returned
    completed_tasks = [task for task in tasks if task.completed]
    #the filtered function for starred_tasks is returned
    starred_tasks = [task for task in tasks if task.starred]

    return render_template(
        'home.html', 
        user=current_user, 
        tasks=tasks, 
        search_query=search_query,
        tasks_due_today=tasks_due_today,
        completed_tasks=completed_tasks,
        starred_tasks=starred_tasks
    )

#route for the settings page
@views.route('/settings', methods=['GET', 'POST'])
def settings():
    user_preferences = Preferences.query.filter_by(user_id=current_user.id).first()

    if not user_preferences:
        user_preferences = Preferences(
            user_id=current_user.id,
            weight_due_date=0.25,
            weight_duration=0.25,
            weight_priority=0.25,
            weight_difficulty=0.25
        )
        db.session.add(user_preferences)
        db.session.commit()

    if request.method == 'POST':
        try:
            weight_due_date = float(request.form.get('weight_due_date', 0))
            weight_duration = float(request.form.get('weight_duration', 0))
            weight_priority = float(request.form.get('weight_priority', 0))
            weight_difficulty = float(request.form.get('weight_difficulty', 0))

            total_weight = weight_due_date + weight_duration + weight_priority + weight_difficulty

            if total_weight != 1:
                flash("The total of all weightings must equal 1. Please adjust your values.", category="error")
                return redirect(url_for('views.settings'))

            user_preferences.weight_due_date = weight_due_date
            user_preferences.weight_duration = weight_duration
            user_preferences.weight_priority = weight_priority
            user_preferences.weight_difficulty = weight_difficulty
            db.session.commit()

            flash("Preferences updated successfully!", category="success")
        except ValueError:
            flash("Invalid input. Please enter numeric values.", category="error")
            return redirect(url_for('views.settings'))

        if not user_preferences:
            user_preferences = Preferences(
                user_id=current_user.id,
                weight_due_date=0.25,
                weight_duration=0.25,
                weight_priority=0.25,
                weight_difficulty=0.25
            )
        db.session.add(user_preferences)
        db.session.commit()

    return render_template('settings.html', user=current_user, user_preferences=user_preferences)
