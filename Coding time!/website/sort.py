#import flask methods for frontend communication
from flask import Blueprint, render_template, flash, redirect, url_for
#flask login imported for managing the state of users in session
from flask_login import current_user
#imported to manage datetime variables
from datetime import datetime
#imported for operations to and from the database
from . import db
from .models import Task, Preferences
#global variable to establish the current date
now = datetime.utcnow()

sort = Blueprint('sort', __name__)

#used to normalize the scale of the task (we equalize the range of all the attributes)
def normalise(tasks):

    #max in this case defines the 'largest' variable in the variable type
    max_due_date = max((task.due_date for task in tasks), default=now)
    max_duration = max((task.duration for task in tasks), default=1)
    max_priority = max((int(task.priority) for task in tasks), default=1) 
    max_difficulty = max((int(task.difficulty) for task in tasks), default=1) 

    #otherwise, if no tasks exists, an empty list is returned
    if not tasks:
        return []
    
    normalised = []
    for task in tasks:

        if task.completed:
            #completed tasks set to 0 so they are not sorted
            normalised.append({
                "task": task,
                "due_date": 0,
                "duration": 0,
                "priority": 0,
                "difficulty": 0
            })
            continue
        
        days_left = (task.due_date - now).days
        last_due_date = (max_due_date - now).days if max_due_date != now else 1

        #tasks due later are represented by proportional values to ensure fair weightings
        normalised.append({
            "task": task,
            "normalised_due_date": 1 - (days_left / last_due_date) if last_due_date != 0 else 0,
            "normalised_duration": 1 - (task.duration / max_duration) if max_duration != 0 else 0,
            "normalised_priority": 1 - (int(task.priority) / max_priority) if max_priority != 0 else 0,
            "normalised_difficulty": 1 - (int(task.difficulty) / max_difficulty) if max_difficulty != 0 else 0,
        })

    return normalised

#the function assigns a proportional value to each of the task attributes
def calculate_scores(tasks, preferences):

    #normalised task scores retrieved
    normalised_tasks = normalise(tasks)
    normalised_tasks = [task_data for task_data in normalised_tasks if not task_data["task"].completed]

    #the weights are imported from the database
    weights = {
        "due_date": preferences.due_date_weight,
        "duration": preferences.duration_weight,
        "priority": preferences.priority_weight,
        "difficulty": preferences.difficulty_weight,
    }

    #using the imported data, the function can then assign a score for each task
    #the score is based on the task's attribute total from their weighting
    scored_tasks = [
        (task_data["task"], sum(weights[key] * task_data.get("normalised_{key}",0) for key in weights))
        for task_data in normalised_tasks
    ]

    #each tuple is checked for the score using the lambda function
    #the reverse=True variable is done to sort the tasks in descending order
    return [task for task, _ in sorted(scored_tasks, key=lambda x: x[1], reverse=True)]

#adjust_weights gives the function some dynamcy when used as it adapts to user behaviour
def adjust_weights(preferences, completed_tasks):

    #for overdue tasks, the due_date weighting receives an additional 0.05+
    if any(task.due_date and task.due_date < now for task in completed_tasks):
        preferences.due_date_weight += 0.05
    #for long tasks, the duration weighting receives an additional 0.03+
    if any(task.duration and task.duration > 500 for task in completed_tasks):
        preferences.duration_weight -= 0.03

    #if one attribute is given a higher weight, the others are proportionally reduced to maintain balance
    total = sum([preferences.due_date_weight, preferences.duration_weight,
                preferences.priority_weight, preferences.difficulty_weight])

    #weights divided by total to give a proportional percentage
    if total > 0:
        preferences.due_date_weight /= total
        preferences.duration_weight /= total
        preferences.priority_weight /= total
        preferences.difficulty_weight /= total

    db.session.commit()

#sort-task function is responsible for sorting the user functions based on the weights
@sort.route('/sort-tasks', methods=['GET', 'POST'])
def sort_tasks():

    #makes sure the function is inactive if user not logged in
    if not current_user.is_authenticated:
        flash("You need to log in to sort tasks.", category="error")
        return redirect(url_for('auth.login'))

    #retrieves the user preferences from the preferences table
    preferences = Preferences.query.filter_by(user_id=current_user.id).first()
    #activates if the preferences are not set
    #they are required for the tasks to run
    if not preferences:
        flash("Please set your preferences before sorting the tasks.", category="warning")
        return redirect(url_for('views.home'))
    #task list retrieved
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    #if there are no tasks present, the user is told to add some
    if not tasks:
        flash("There are no tasks that can be sorted. Add more before trying this feature!", category="error")
        return redirect(url_for('views.home'))
    #the sorted tasks care then sorted based off of the values from calculate_scores
    sorted = calculate_scores(tasks, preferences)

    #maps used to map back the original string value to difficulty and priority
    priority_map = {1: "High", 2: "Medium", 3: "Low"}
    difficulty_map = {1: "Easy", 2: "Medium", 3: "Hard"}
    #the values are then retrived
    for task in sorted:
        task.priority_str = priority_map.get(task.priority, "Low")
        task.difficulty_str = difficulty_map.get(task.difficulty, "Easy")

    #sort will then sort the tasks based on the weighted score
    #duration is then made to appear in ascending order if used
    #so the quickest task appears first
    sort = calculate_scores(tasks, preferences)
    flash("Your tasked have been sorted!", category="success")

    return render_template('home.html', user=current_user, tasks=sort)
