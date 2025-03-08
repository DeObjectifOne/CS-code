from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import current_user
from datetime import datetime
from . import db
from .models import Task, Preferences
now = datetime.utcnow()

sort = Blueprint('sort', __name__)

#used to normalize the scale of the task (we equalize the range of all the attributes)
#so that attributes with larger ranges don't take precedence over ones with smaller ranges
def normalise(tasks):

    #max in this case defines the 'largest' variable in the variable type
    #this allows the largest duration variable to be set to 1, so all other variables are indexed proportionally
    max_due_date = max((task.due_date for task in tasks), default=now)
    max_duration = max((task.duration for task in tasks), default=1)
    max_priority = max((int(task.priority) for task in tasks), default=1) 
    max_difficulty = max((int(task.difficulty) for task in tasks), default=1) 

    if not tasks:
        return []

    #calculations to normalise each task
    #the goal is to find suitable values for the amount of tasks the user has
    #due_date uses reverse scaling (the task due the soonest has a value of 1)

    #if the task is completed, all attributes are set to 0
    #this avoids sorting a task which can be considered unecessary
    normalised_tasks = []
    for task in tasks:
        if task.completed:
            normalised_tasks.append({
                "task": task,
                "due_date": 0,
                "duration": 0,
                "priority": 0,
                "difficulty": 0
            })
            continue
        
        denominator = (max_due_date - now).days if max_due_date else 0
        #tasks due later are represented by proportional values to ensure fair weightings
        #for priority, duration and difficulty, the variable with the 'highest' gains a value of 1 for weighting
        #the other variables get a value proportional to the max value to ensure proportional representation
        normalised_tasks.append({
            "task": task,
            "normalised_due_date": 1 - ((task.due_date - now).days / denominator) if denominator != 0 else 0,
            "normalised_duration": 1 - (task.duration / max_duration) if max_duration != 0 else 0,
            "normalised_priority": 1 - (int(task.priority) / max_priority) if max_priority != 0 else 0,
            "normalised_difficulty": 1 - (int(task.difficulty) / max_difficulty) if max_difficulty != 0 else 0,
        })

    return normalised_tasks

#the function assigns a proportional value to each of the task attributes
#this is done to ensure everything is ordered in accordance with user preferences
#this also optimises the sorting variables more
def calculate_scores(tasks, preferences):

    normalised_tasks = normalise(tasks)
    normalised_tasks = [task_data for task_data in normalised_tasks if not task_data["task"].completed]

    #the weights are imported from the database
    #the weights are used to determine the user preferences for each attribute
    #this means sorting can be adjusted to prefer one attribute over another
    weights = {
        "due_date": preferences.due_date_weight,
        "duration": preferences.duration_weight,
        "priority": preferences.priority_weight,
        "difficulty": preferences.difficulty_weight,
    }

    #using the imported data, the function can then assign a score for each task
    #the score is based on the task's attribute total from their weighting
    #to calculate a total score, the data for a task's attribute is multiplied by the weight data
    #the higher overall score a task gets, the more 'important' it is to the user
    #hence, that task has a higher chance of getting sorted first
    scored_tasks = [
        (task_data["task"], sum(weights[key] * task_data.get("normalised_{key}",0) for key in weights))
        for task_data in normalised_tasks
    ]

    #each tuple is checked for the score using the lambda function
    #the reverse=True variable is done to sort the tasks in descending order
    #this is so the most immediate task is shown first
    return [task for task, _ in sorted(scored_tasks, key=lambda x: x[1], reverse=True)]

#adjust_weights gives the function some dynamcy when used as it adapts to user behaviour
#makes the function a bit more effective at task sorting
def adjust_weights(preferences, completed_tasks):

    #the variable overdue is used to check for tasks the user has overdue
    #the variable long_tasks is used to check for tasks that are considered long (in this case 4 hours)
    #if the variable is active, the due_date weighting receives an additional 0.05
    #if the variable is active the duration weighting receives an additional 0.03
    if any(task.due_date and task.due_date < now for task in completed_tasks):
        preferences.due_date_weight += 0.05
    if any(task.duration and task.duration > 500 for task in completed_tasks):
        preferences.duration_weight -= 0.03


    #to account for any variable increases, the weights are adjusted again
    #so if one attribute is given a higher weight, the others are proportionally reduced to maintain balance
    total = sum([preferences.due_date_weight, preferences.duration_weight,
                preferences.priority_weight, preferences.difficulty_weight])

    if total:
        preferences.due_date_weight /= total
        preferences.duration_weight /= total
        preferences.priority_weight /= total
        preferences.difficulty_weight /= total
    
    db.session.commit()

#sort-task function is responsible for sorting the user functions based on the weights
#its also responsible for rendering them in html upon completion
@sort.route('/sort-tasks', methods=['GET', 'POST'])
def sort_tasks():

    if not current_user.is_authenticated:
        flash("You need to log in to sort tasks.", category="error")
        return redirect(url_for('auth.login'))

    #retrieves the user preferences from the preferences table
    user_preferences = Preferences.query.filter_by(user_id=current_user.id).first()

    #activates if the preferences are not set
    #they are required for the tasks to run
    if not user_preferences:
        flash("Please set your preferences before sorting the tasks.", category="warning")
        return redirect(url_for('views.home'))

    #task list retrieved
    tasks = Task.query.filter_by(user_id=current_user.id).all()

    #if there are no tasks present, the user is told to add some
    if not tasks:
        flash("There are no tasks that can be sorted. Add more before trying this feature!", category="error")
        return redirect(url_for('views.home'))

    #the sorted tasks care then sorted based off of the values from calculate_scores
    sorted_tasks = calculate_scores(tasks, user_preferences)

    #maps used to map back the original string value to difficulty and priority
    priority_map = {1: "High", 2: "Medium", 3: "Low"}
    difficulty_map = {1: "Easy", 2: "Medium", 3: "Hard"}

    #the values are then retrived
    for task in sorted_tasks:
        task.priority_str = priority_map.get(task.priority, "Low")
        task.difficulty_str = difficulty_map.get(task.difficulty, "Easy")

    #sort will then sort the tasks based on the weighted score
    #duration is then made to appear in ascending order if used
    #so the quickest task appears first
    sort = calculate_scores(tasks, user_preferences)
    flash("Your tasked have been sorted!", category="success")

    return render_template('home.html', user=current_user, tasks=sort)
