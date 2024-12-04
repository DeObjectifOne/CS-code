from flask import Blueprint, render_template, flash, redirect, url_for, request

from flask_login import login_required, current_user

from datetime import datetime

from . import db

from .models import Task, Preferences

sort = Blueprint('sort', __name__)

#used to normalize the scale of the task
#meaning we equalize the range of all the attributes
#so that attributes with larger ranges don't take precedence over ones with smaller ranges
#this allows for smaller values to be more impactful when comparing weights
def normalize_tasks(tasks):

    #max in this case defines the 'largest' variable in the variable type
    #for example, max_duration would be using the longest duration as the max
    #this allows the largest duration variable to be set to 1, so all other variables are indexed proportionally
    max_due_date = max((task.due_date for task in tasks), default=datetime.utcnow())
    max_duration = max((task.duration for task in tasks), default=1)
    max_priority = max((int(task.priority) for task in tasks), default=1) 
    max_difficulty = max((int(task.difficulty) for task in tasks), default=1) 

    normalized_tasks = []
    for task in tasks:
        #calculations to normalize each task
        #the goal is to find suitable values for the amount of tasks the user has
        #due_date uses reverse scaling
        #this means that the task due the soonest has a value of 1
        #tasks due later are represented by proportional values to ensure fair weightings
        normalized_due = (1 - ((task.due_date - datetime.utcnow()).days / (max_due_date - datetime.utcnow()).days)) if task.due_date else 0
        #for priority, duration and difficulty, the variable with the 'highest' gains a value of 1 for weighting
        #the other variables get a value proportional to the max value to ensure proportional representation
        normalized_duration = task.duration / max_duration
        normalized_priority = int(task.priority) / max_priority
        normalized_difficulty = int(task.difficulty) / max_difficulty

        #the tasks are all appended to the original task
        #so the task has its normalized attributes
        #makes for easier mapping of values back to the respective task
        normalized_tasks.append({
            "task": task,
            "due_date": normalized_due,
            "duration": normalized_duration,
            "priority": normalized_priority,
            "difficulty": normalized_difficulty
        })

    return normalized_tasks

#calculate_task_scores assigns a proportional value to each of the task attributes
#this is done to ensure everything is ordered in accordance with user preferences
#this also optimises the sorting variables more
def calculate_task_scores(tasks, preferences):
    normalized_tasks = normalize_tasks(tasks)

    #the weights are imported from the database
    #the weights are used to determine the user preferences for each attribute
    #this means sorting can be adjusted to prefer one attribute over another
    weights = {
        "due_date": preferences.weight_due_date,
        "duration": preferences.weight_duration,
        "priority": preferences.weight_priority,
        "difficulty": preferences.weight_difficulty,
    }

    #using the imported data, the function can then assign a score for each task
    #the score is based on the task's attribute total from their weighting
    scored_tasks = []
    for task_data in normalized_tasks:
        task = task_data["task"]
        score = (
            #to calculate a total score, the data for a task's attribute is multiplied by the weight data
            #the higher overall score a task gets, the more 'important' it is to the user
            #hence, that task has a higher chance of getting sorted first
            weights["due_date"] * task_data["due_date"] +
            weights["duration"] * task_data["duration"] +
            weights["priority"] * task_data["priority"] +
            weights["difficulty"] * task_data["difficulty"]
        )
        #the totals for each task are appended to the database
        #they're added in separate tuples
        scored_tasks.append((task, score))

    #the function then looks inside each tuple for the second element in each tuple (the score)
    #this is done using the Lambda function
    #the reverse=True variable is done to sort the tasks in descending order
    #this is so the most immediate task is shown first
    scored_tasks.sort(key=lambda x: x[1], reverse=True)
    return [task[0] for task in scored_tasks]

#adjust_weights gives the function some dynamcy when used
#this makes the sorting somewhat smart as it's made to adapt to user behaviour
#makes the function a bit more effective at task sorting
def adjust_weights(preferences, completed_tasks):
    #the variable overdue_task is used to check for tasks the user has overdue
    overdue_tasks = [task for task in completed_tasks if task.due_date and task.due_date < datetime.utcnow()]
    #the variable long_tasks is used to check for tasks that are considered long (in this case 4 hours)
    long_tasks = [task for task in completed_tasks if task.duration > 4]

    #if the variable is active, the due_date weighting receives an additional 0.05
    #this makes the due_date variable more important than the other 3 attributes
    #this puts more emphesis on the need to complete the overdue task
    if overdue_tasks:
        preferences.weight_due_date += 0.05
    #if the variable is activem the duration weighting receives an additional 0.03
    #this makes the duration variable less important than the other 3 attributes
    #this puts more emphesis on quicker tasks
    if long_tasks:
        preferences.weight_duration -= 0.03

    #to account for any variable increases, the weights are adjusted again
    #so if one attribute is given a higher weight, the others are proportionally reduced to maintain balance
    total_weight = (
        preferences.weight_due_date +
        preferences.weight_duration +
        preferences.weight_priority +
        preferences.weight_difficulty
    )

    preferences.weight_due_date /= total_weight
    preferences.weight_duration /= total_weight
    preferences.weight_priority /= total_weight
    preferences.weight_difficulty /= total_weight

    db.session.commit()

#sort-task function is responsible for sorting the user functions based on the weights
#its also responsible for rendering them in html upon completion
@sort.route('/sort-tasks', methods=['GET', 'POST'])
def sort_tasks():

    #retrieves the user preferences from the preferences table
    user_preferences = Preferences.query.filter_by(user_id=current_user.id).first()

    #activates if the preferences are not set
    #they are required for the tasks to run
    if not user_preferences:
        flash("Please set your preferences before sorting tasks.", category="warning")
        return redirect(url_for('views.home'))

    #task_query retrieves all the user's tasks from the task table
    #the filter_by option makes sure that the tasks for only that user are fetched
    tasks_query = Task.query.filter_by(user_id=current_user.id).all()
    #sorted_tasks will then sort the tasks based on the weighted score
    #duration is then made to appear in ascending order if used
    #so the quickest task appears first
    sorted_tasks = sorted(tasks_query, key=lambda task: task.duration)

    return render_template('home.html', user=current_user, tasks=sorted_tasks)
