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
#imports scores from sort.py so they can be fed back to sort.py from settings
from .sort import calculate_scores
#used to calculate the repositioning of tasks
from .utils import reposition_task

#blueprint for the views template
views = Blueprint('views', __name__)

#route for the home page
@views.route('/home', methods=['GET', 'POST'])
@login_required
def home():

    #search query is empty for user entry
    query = ""
    if request.method == 'POST':
        query = request.form.get('search', "").strip()
        #tasks are filtered for specific characters
        tasks = Task.query.filter(
            Task.user_id == current_user.id,
            #uses the ilike function to filter out words specifically
            Task.details.ilike(f"%{query}%")
        ).all()
    else:
        #displays all the user's tasks regardless of the search function
        tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.position).all()

    #user preferences imported to the home page to be used
    user_preferences = Preferences.query.filter_by(id=current_user.id).first()
    if user_preferences:
        tasks = calculate_scores(tasks, user_preferences)

    #mapping done to change the integers into string values
    priority_map = {1: "High", 2: "Medium", 3: "Low"}
    difficulty_map = {1: "Easy", 2: "Medium", 3: "Hard"}
    for task in tasks:
        task.priority_str = priority_map.get(task.priority, "Low")
        task.difficulty_str = difficulty_map.get(task.difficulty, "Easy")

    #the filtered function for tasks_due_today is returned to the user
    today = datetime.utcnow().date()
    tasks_due_today = [task for task in tasks if task.due_date and task.due_date.date() == today]
    #the filtered function(s) are returned
    completed = [task for task in tasks if task.completed]
    starred = [task for task in tasks if task.starred]

    #returns the user's home template with all the variables
    return render_template(
        'home.html', 
        user=current_user, 
        tasks=tasks, 
        query=query,
        tasks_due_today=tasks_due_today,
        completed_tasks=completed,
        starred_tasks=starred
    )

#route for the settings page
@views.route('/settings', methods=['GET', 'POST'])
def settings():

    preferences = Preferences.query.filter_by(user_id=current_user.id).first()
    #if user preferences do not exist, the defaults from the database are used instead
    #the default value for each is 0.25
    if not preferences:
        preferences = Preferences(user_id=current_user.id)
        db.session.add(preferences)
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
            total_weight = sum([due_date_weight, duration_weight, priority_weight, difficulty_weight])
            if total_weight != 1:
                flash("The total of all weightings must equal 1, please adjust your values!", category="danger")
                return redirect(url_for('views.settings'))
            #the new weights are now the user's default weights during their next session
            preferences.due_date_weight = due_date_weight
            preferences.duration_weight = duration_weight
            preferences.priority_weight = priority_weight
            preferences.difficulty_weight = difficulty_weight
            db.session.commit()
            flash("Your preferences have been updated successfully!", category="success")

        except ValueError:
            #used so that all non-float characters are rejected
            flash("Invalid input, please enter numeric values!", category="danger")
            return redirect(url_for('views.settings'))

    return render_template('settings.html', user=current_user, user_preferences=preferences)


#route for manual task moving
@views.route('/reposition', methods=['POST'])
@login_required
def reposition():

    #keeps track of tasks and their requested position
    id = request.form.get('task_id')
    direction = request.form.get('direction')

    if id and direction:
        #function call made to reposition the task
        task = reposition_task(current_user.id, id, direction)
        #if the movement is successful, a message is sent
        if task:
            flash(f"'{task.details}' has been moved {direction}!", category="success")
        #otherwise it is deemed a failure
        else:
            flash("An error had occured and your task could not be moved!", category="danger")
    else:
        flash("Invalid task or input made, please try again!", category="danger")

    return redirect(url_for('views.home'))
