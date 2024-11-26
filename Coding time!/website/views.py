#import flask modules for route handling and get and post requests
from flask import Blueprint, render_template, request, flash, redirect, url_for

#imports the database for data handling
from . import db

#import the user table to check for pre-existing users
from .models import Task

#used to handle user data depending on their action
from flask_login import login_required, current_user

from datetime import datetime

#blueprint for the views template
views = Blueprint('views', __name__)

#route for the home page
@views.route('/home')
@login_required
def home():

    #all the inputted tasks are displayed on the home page
    from .models import Task, User
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('home.html', user=current_user, tasks=tasks)

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

@views.route('/edit-task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):

    task = Task.query.get_or_404(task_id)
    
    if task.user_id != current_user.id:
        flash("You are not authorized to edit this task.", category="error")
        return redirect(url_for('views.home'))
    
    if request.method == 'POST':
        task.details = request.form.get('details')
        task.duration = request.form.get('duration')
        task.due_date = request.form.get('due_date')
        
        if task.due_date:
            try:
                task.due_date = datetime.fromisoformat(task.due_date)
            except ValueError:
                flash("Invalid date format. Please try again.", category="error")
                return redirect(url_for('views.edit_task', task_id=task_id))
        
        task.priority = request.form.get('priority')
        task.difficulty = request.form.get('difficulty')
        
        db.session.commit()
        flash("Task updated successfully!", category="success")
        return redirect(url_for('views.home'))
    
    return render_template('editing.html', task=task)

@views.route('/delete-task', methods=['POST'])
def delete_task():
    task_id = request.form.get('task_id')  # Get the task ID from the form data

    if not task_id:
        return "Task ID is required", 400

    task = Task.query.get(task_id)  # Fetch the task from the database

    if task and task.user_id == current_user.id:  # Ensure the task belongs to the logged-in user
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted successfully!", category="success")
        return redirect(url_for('views.home'))  # Redirect back to the home page

    flash("Task not found or you don't have permission to delete it.", category="error")
    return redirect(url_for('views.home'))
