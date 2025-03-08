#import flask modules for route handling and get and post requests
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
#imports the database for data handling
from . import db
#import the task table to import data from it
from .models import Task, Preferences
#used to handle user data depending on their action
from flask_login import login_required, current_user
#special import for the due_date function specifically
from datetime import datetime
from .sort import calculate_scores
from .utils import reposition_task

#blueprint for the views template
views = Blueprint('views', __name__)

#route for the home page
@views.route('/home', methods=['GET', 'POST'])
@login_required
def home():


    #search query is empty for user entry
    search_query = ""

    if request.method == 'POST':
        search_query = request.form.get('search', "").strip()

        #tasks are filtered for specific characters
        tasks = Task.query.filter(
            #confirmation to ask if task id matches the user's current id
            Task.user_id == current_user.id,
            #uses the ilike function to filter out words specifically
            Task.details.ilike(f"%{search_query}%")
        ).all()
    else:
        #displays all the user's tasks regardless of the search function
        tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.position).all()

    user_preferences = Preferences.query.filter_by(id=current_user.id).first()
    if user_preferences:
        tasks = calculate_scores(tasks, user_preferences)

    priority_map = {1: "High", 2: "Medium", 3: "Low"}
    difficulty_map = {1: "Easy", 2: "Medium", 3: "Hard"}

    for task in tasks:
        task.priority_str = priority_map.get(task.priority, "Low")
        task.difficulty_str = difficulty_map.get(task.difficulty, "Easy")

    #the filtered function for tasks_due_today is returned to the user
    today = datetime.utcnow().date()
    tasks_due_today = [task for task in tasks if task.due_date and task.due_date.date() == today]
    #the filtered function for completed_tasks is returned
    #the filtered function for starred_tasks is returned
    completed_tasks = [task for task in tasks if task.completed]
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

    #if user preferences do not exist, the defaults from the database are used instead
    #the default value for each is 0.25
    if not user_preferences:
        user_preferences = Preferences(user_id=current_user.id)
        db.session.add(user_preferences)
        db.session.commit()

    if request.method == 'POST':
        try:

            #user weights are retrieved in float form
            #so they can all add up to one
            due_date_weight = float(request.form.get('due_date_weight', 0))
            duration_weight = float(request.form.get('duration_weight', 0))
            priority_weight = float(request.form.get('priority_weight', 0))
            difficulty_weight = float(request.form.get('difficulty_weight', 0))

            #the weights are checked to make sure they all add up to one
            #otherwise the user has to readjust them
            total_weight = due_date_weight + duration_weight + priority_weight + difficulty_weight
            if total_weight != 1:
                flash("The total of all weightings must equal 1, please adjust your values!", category="error")
                return redirect(url_for('views.settings'))

            #the new weights are now the user's default weights during their next sesson
            user_preferences.due_date_weight = due_date_weight
            user_preferences.duration_weight = duration_weight
            user_preferences.priority_weight = priority_weight
            user_preferences.difficulty_weight = difficulty_weight
            db.session.commit()

            flash("Your preferences have been updated successfully!", category="success")
        except ValueError:
            #used so that all non-float characters are rejected
            #the only character that can be accepted but is not a float is one\
            #if the rest of the weights are set to zero
            flash("Invalid input, please enter numeric values!", category="error")
            return redirect(url_for('views.settings'))

    return render_template('settings.html', user=current_user, user_preferences=user_preferences)


#route for manual task moving
@views.route('/reposition', methods=['POST'])
@login_required
def reposition():

    #keeps track of tasks and their requested position
    task_id = request.form.get('task_id')
    direction = request.form.get('direction')

    if task_id and direction:

        #function call made to reposition the task
        task = reposition_task(current_user.id, task_id, direction)

        #if the movement was successful, a message is sent
        if task:
            flash(f"'{task.details}' has been moved {direction}!", category="success")
        #otherwise it is deemed a failure
        else:
            flash("An error had occured and your task could not be moved!", category="error")
    else:
        flash("Invalid task or input made, please try again!", category="error")

    return redirect(url_for('views.home'))
