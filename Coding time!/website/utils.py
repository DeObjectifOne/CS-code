#import flask modules for route handling and get and post requests
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
#imports the database for data handling
from . import db
#import the task table to import data from to and from it
from .models import Task
#used to handle user data depending on their action in or out the website
from flask_login import login_required, current_user
#special import for the due_date function specifically
from datetime import datetime, date
from sqlalchemy import func

#blueprint to send functions to __init__.py
utils = Blueprint('utils', __name__)

#function that allows the user to make a new task
@utils.route('/creation', methods=['GET', 'POST'])
@login_required
def create_task():
    
    try:
            #the user inputs on creation.html are retrieved
            if request.method == 'POST':

                details = request.form.get("details")
                duration = float(request.form.get('duration', 0))
                due_date_str = request.form.get("due_date")
                #the priority and difficulty variables are mapped out
                priority_map = {"Low": 3, "Medium": 2, "High": 1}
                difficulty_map = {"Easy": 1, "Medium": 2, "Hard": 3}
                #the mapped variables are then remapped to the user's preference
                #so they can be properly sorted when the user eventually sorts them
                priority = priority_map.get(request.form.get('priority'), 1)  
                difficulty = difficulty_map.get(request.form.get('difficulty'), 1)  
                #the due_date is imported as a datetime variable for proper sorting
                due_date = datetime.fromisoformat(due_date_str)
                notes = request.form.get('notes')

                #this makes sure the user has an input in task details
                if not details:
                    flash("Task details are required", category='error')
                else:
                    #a new task variable is created
                    new = Task(
                        details=details,
                        duration=duration,
                        due_date=due_date,
                        priority=priority,
                        difficulty=difficulty,
                        notes=notes,
                        user_id=current_user.id
                    )
                    db.session.add(new)
                    db.session.commit()
                    flash("Your tasks have been created successfully", category='success')
                    #the user is then redirected to the home page
                    return redirect(url_for('views.home'))
    
    except ValueError:
        #if there is an invalid input from the user, this comes up
        flash("Invalid input, please try again!", category = "danger")
        return redirect(url_for('utils.create_task'))

    return render_template('creation.html', user=current_user)

#function to edit a task
@utils.route('/edit-task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):

    #the task itself is retrieved using a query from the task table
    task = Task.query.get_or_404(task_id)

    #check to make sure the task the user is editing is theirs
    if task.user_id != current_user.id:
        flash("You are not allowed to edit this task!", category="danger")
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        #otherwise, the user's details are retrieved
        task.details = request.form.get('details')
        task.duration = float(request.form.get('duration', 0))
        task.due_date = request.form.get('due_date')
        task.notes = request.form.get('notes')

        #the priority and difficulty variables are retrieved by using their mapped variables
        #can be used for automatic task sorting
        priority_map = {"Low": 3, "Medium": 2, "High": 1}
        difficulty_map = {"Easy": 1, "Medium": 2, "Hard": 3}
        task.priority = priority_map.get(request.form.get('priority'), 1)
        task.difficulty = difficulty_map.get(request.form.get('difficulty'), 1)

        #due date converted to datetime if it was provided
        if task.due_date:
            try:
                task.due_date = datetime.fromisoformat(task.due_date)
            except ValueError:
                flash("Invalid date format. Please try again.", category="error")
                return redirect(url_for('utils.edit_task', task_id=task_id))

        #the changes are then saved to the database
        db.session.commit()
        flash("You're tasks have been updated successfully!", category="success")
        return redirect(url_for('views.home'))
    
    return render_template('editing.html', task=task)

#function for deleting a task
@utils.route('/delete-task', methods=['POST'])
def delete_task():

    #the task itself has to be retrieved first
    task_id = request.form.get('task_id') 
    #if the task id is not returned, the user is flashed a message
    if not task_id:
        return "Task ID is required", 400
    #the task id is then retrieved from the Task table
    task = Task.query.get(task_id) 

    #the task id is then checked to see if the task is linked to the user table
    #if it's linked to the table, then the database is cleared of the task
    if task and task.user_id == current_user.id:  
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted successfully!", category="success")
        return redirect(url_for('views.home'))

    #the user is flashed with an error message if the task isn't unable to be deleted
    flash("Task not found or you don't have permission to delete it.", category="error")
    return redirect(url_for('views.home'))

#task filtering functions
@utils.route('/filter', methods=['GET', 'POST'])
def filter_tasks():

    #the filter type is retrieved and the query is started
    filter_type = request.form.get('filter')
    query = Task.query.filter_by(user_id=current_user.id)

    #the filter types are then applied to the user choice
    if filter_type == 'creation_date':
        #sort by date of creation
        query = query.order_by(Task.creation_date.desc())
    elif filter_type == 'due_date':
        #filtered for tasks that are due today
        today = date.today().isoformat()
        query = query.filter(func.strftime('%Y-%m-%d', Task.due_date) == today) 
    elif filter_type == 'completed':
        #filtered for tasks that have been completed
        query = query.filter(Task.completed == True)
    elif filter_type == 'starred':
        #filtered for tasks that have been starred
        query = query.filter(Task.starred == True)
    else:
        #default 'filter' - meaning none
        query = query.filter_by(user_id=current_user.id)
    tasks = query.all()

    return render_template('home.html', user=current_user, tasks=tasks)

#update task status function
@utils.route('update-task', methods=['POST'])
def update_task():

    #the last action performed on a task is taken into account
    id = request.form.get('task_id')
    action = request.form.get('action')
    task = Task.query.get(id)

    #if the action is complete, the variable is set to true
    if task and task.user_id == current_user.id:
        if action == "complete":
            task.completed = not task.completed
        #if the action is star, the variable is set to true
        elif action == "star":
            task.starred = not task.starred
        db.session.commit()
        #message sent to notify the user that it worked
        flash(f"Task '{task.details}' updated successfully", category="success")
    else:
        #message sent incase of failure to update task
        flash("Task not found or unable to be updated, try again!", category='danger')

    return redirect(url_for('views.home'))

@utils.route('/reposition-task', methods=['POST'])
def reposition_task(user_id, task_id, direction):

    #user's current tasks retrieved
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    #if there are no tasks to move, the function outputs nothing
    if not task:
        return None

    #task list retrieved with the positions of each task having been established
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.position).all()
    # Find the current task's position in the list
    index = tasks.index(task)

    if direction == 'up' and index > 0:
        # Swap the task with the one above
        task[index], task[index - 1] = task[index - 1], task[index]
    elif direction == 'down' and index < len(task) - 1:
        # Swap the task with the one below
        task[index], task[index + 1] = task[index + 1], task[index]

    # Update the position of each task
    for idx, t in enumerate(task):
        t.position = idx
    db.session.commit()

    return task

#function to record the new task order in the database
@utils.route("/update-order", methods=["POST"])
def update_order():

    #retrieves all recent task positions
    data = request.json
    #all new position values are imported and retaken
    for item in data:
        task = Task.query.get(item["id"])
        if task:
            task.position = item["position"]
    db.session.commit()

    #message returned to tell the user the task order has been updated
    return jsonify({"message": "Your task order has updated successfully!"})

