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
@views.route('/home')
@login_required
def home():

    #search query is empty for user entry
    search_query = ""

    if request.method == 'POST':
        search_query = request.form.get('search', "")

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
@views.route('/settings')
def settings():
    return render_template('settings.html')

#Creates a method that lets the user add tasks to their database
@views.route('/creation', methods=['GET', 'POST'])
@login_required
def create_task():

    try:
        
        #retrieves the data from creation.html 
        if request.method == 'POST':
            details = request.form.get("details")
            duration = request.form.get("duration")
            due_date_str = request.form.get("due_date")
            priority = request.form.get("priority")
            difficulty = request.form.get("difficulty")

            #used to convert the due_date into a datetime variable
            #this is so it can be displayed on the main page
            due_date = datetime.fromisoformat(due_date_str)

            #checks if the data has been imported
            if not details:
                flash("Task details are required", category='error')
            else:
                
                #all the data is imported to the database
                from .models import Task
                new_task = Task(
                    details=details,
                    duration=duration,
                    due_date=due_date,
                    priority=priority,
                    difficulty=difficulty,
                    user_id=current_user.id
                )
                #the changes are commited
                #the user then returns to the home page
                db.session.add(new_task)
                db.session.commit() 
                flash("Task created successfully", category='success')
                return redirect(url_for('views.home'))
    
    #an error is displayed if the data could not be imported
    except ValueError:
        flash("Invalid input, try again", category="error")
        return redirect(url_for('create_task'))

    return render_template('creation.html', user=current_user)

#task editing function
@views.route('/edit-task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):

    #task is retrieved using its id
    task = Task.query.get_or_404(task_id)

    #permission denied if the task id does not match with the user's current id
    if task.user_id != current_user.id:
        flash("You are not authorized to edit this task.", category="error")
        return redirect(url_for('views.home'))

    #the task details are retrieved
    if request.method == 'POST':
        task.details = request.form.get('details')
        task.duration = request.form.get('duration')
        task.due_date = request.form.get('due_date')

        #special retrieval for the due_date variable
        #due to it being a datetime variable
        #has to be retrieved while retaining the same format
        if task.due_date:
            try:
                task.due_date = datetime.fromisoformat(task.due_date)
            except ValueError:
                #error management if the variable could not be retrieved
                flash("Invalid date format. Please try again.", category="error")
                return redirect(url_for('views.edit_task', task_id=task_id))

        #the rest are retrieved normally
        task.priority = request.form.get('priority')
        task.difficulty = request.form.get('difficulty')

        #the changes the user made are then added to the home page
        #if the user does not change a variable, that variable remains unchanged regardless
        db.session.commit()
        flash("Task updated successfully!", category="success")
        return redirect(url_for('views.home'))
    
    return render_template('editing.html', task=task)

#delete task function
@views.route('/delete-task', methods=['POST'])
def delete_task():
    task_id = request.form.get('task_id') #gets task if for task recognition
    if not task_id:
        return "Task ID is required", 400

    task = Task.query.get(task_id)

    #if the task matches the id and the user id
    #the function goes ahead
    if task and task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted successfully!", category="success")
        return redirect(url_for('views.home')) 

    #made incase of error
    flash("Task not found or you don't have permission to delete it.", category="error")
    return redirect(url_for('views.home'))

#function to filter the user tasks
@views.route('/filter', methods=['GET', 'POST'])
def filter_tasks():

    filter_type = request.form.get('filter')

    #filter types by using the models.py variables
    #they are all ordered in accordance with said variable
    if filter_type == 'creation_date':
        tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.creation_date.desc()).all()
    elif filter_type == 'due_date':
        tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.due_date.desc()).all()
    elif filter_type == 'completed':
        tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.completed.desc()).all()
    elif filter_type == 'starred':
        tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.starred.desc()).all()
    else:
        tasks = Task.query.filter_by(user_id=current_user.id).all()

    return render_template ('home.html', user=current_user, tasks=tasks)

#function to confirm if a task is completed/starred
@views.route('update-task', methods=['POST'])
def update_task():

    task_id = request.form.get('task_id')
    action = request.form.get('action')
    task = Task.query.get(task_id)

    #both variables 'completed' and 'starred' are marked as false boolean variables
    #they become true once activated
    #these changes update the user task
    #they can then be sorted by 'tasks completed' or task 'starred'
    if task and task.user_id == current_user.id:
        if action == "complete":
            task.completed = not task.completed
        elif action == "star":
            task.starred = not task.starred
        db.session.commit()
        flash(f"Task '{task.details}' updated successfully", category="success")
    else:
        flash("Task not found or unable to be updated", category='error')

    return redirect(url_for('views.home'))
