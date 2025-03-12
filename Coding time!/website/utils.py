#Blueprint imported so the function can be exported as a package
#render_template imported to load html pages upon user interaction
#request imported so data can be sent and retrieved upon user request
#flash imported for user notifications incase there is an error/success
#redirect import used to send user to webpages upon user interaction
#url_for imported for link referencing in python functions
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
#database imported for user-database interaction
from . import db
#User and Task table imported for user-table interaction
from .models import User, Task
#login_required imported to restrict usage of this function
#this means it cannot be used unless the user is logged in
#current_user imported for session purposes
#allows flask to detect certain users whenever they're using the website
from flask_login import login_required, current_user
#datetime imported for user interactions with datetime variables
#these are the due_date and creation_date variables
from datetime import datetime, date
#blueprint for the util(itie)s template
#can be used for importing purposes
utils = Blueprint('utils', __name__)

from sqlalchemy.sql import text
from sqlalchemy import cast, Date, func

#function that allows the user to make a new task
@utils.route('/creation', methods=['GET', 'POST'])
@login_required
def create_task():
    
    try:
            #the user inputs on creation.html are retrieved
            #the duration variable is retrieved as a float
            #as the user's input will not always be a whole number
            if request.method == 'POST':
                details = request.form.get("details")
                duration = float(request.form.get('duration', 0))
                due_date_str = request.form.get("due_date")

                #the priority and difficulty variables are mapped out
                #this is to make it easier for the sorting algorithm
                #to use these 2 functions during sorting
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
                #as a blank task would be unsearchable
                if not details:
                    flash("Task details are required!", category='danger')
                    return redirect(url_for('utils.create_task'))

                if duration < 0:
                    flash("the duration cannot be a negative value!", category='danger')
                    return redirect(url_for('utils.create_task'))

                if due_date.date() < datetime.today().date():
                    flash("A task cannot be completed in the past!", category='danger')
                    return redirect(url_for('utils.create_task'))

                #a new task variable is created
                #it contains the user's new inputs
                #before assigning them to the user
                #via their id
                new_task = Task(
                    details=details,
                    duration=duration,
                    due_date=due_date,
                    priority=priority,
                    difficulty=difficulty,
                    notes=notes,
                    user_id=current_user.id
                )
                db.session.add(new_task)
                db.session.commit()

                flash("Task created successfully", category='success')
                #the user is then redirected to the home page
                #where they can see their tasks displayed
                #using home.html
                return redirect(url_for('views.home'))
    
    except ValueError:
        #if there is an invalid input from the user, this comes up
        #the user is unable to make the task
        #before being redirected to the same page
        flash("Invalid input, try again", category="error")
        return redirect(url_for('utils.create_task'))

    return render_template('creation.html', user=current_user)

#function to edit a task
@utils.route('/edit-task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):

    #the task itself is retrieved using a query
    #from the task table
    task = Task.query.get_or_404(task_id)

    #check to make sure the task the user is editing is theirs
    #if not, they're unable to progress
    if task.user_id != current_user.id:
        flash("You are not authorized to edit this task.", category="error")
        return redirect(url_for('views.home'))

    #otherwise, the user's details are retrieved
    #similarly to how it was retrieved in create_task
    if request.method == 'POST':
        task.details = request.form.get('details')
        task.duration = float(request.form.get('duration', 0))
        task.due_date = request.form.get('due_date')
        task.notes = request.form.get('notes')

        priority_map = {"Low": 3, "Medium": 2, "High": 1}
        difficulty_map = {"Easy": 1, "Medium": 2, "Hard": 3}

        due_date_str = request.form.get('due_date')
        if due_date_str:
            try:
                task.due_date = datetime.fromisoformat(due_date_str)
            except ValueError:
                flash("Invalid date format. Please try again.", category="error")
                return redirect(url_for('utils.edit_task', task_id=task_id))

        if task.duration < 0:
            flash("the duration cannot be a negative value!", category='danger')
            return redirect(url_for('utils.edit_task', task_id=task_id))

        if task.due_date.date() < datetime.today().date():
            flash("A task cannot be completed in the past!", category='danger')
            return redirect(url_for('utils.edit_task', task_id=task_id))

        #the priority and difficulty variables are retrieved by using their mapped variables
        #can be used for automatic task sorting
        task.priority = priority_map.get(request.form.get('priority'), 1)
        task.difficulty = difficulty_map.get(request.form.get('difficulty'), 1)

        #if all the checks are passed, the user is allowed to POST their task changes
        #the changes are then saved to the database
        #the user is then redirected to home.html
        #where they can see their updated changes
        db.session.commit()
        flash("Task updated successfully!", category="success")
        return redirect(url_for('views.home'))
    
    return render_template('editing.html', task=task)

#function for deleting a task
@utils.route('/delete-task', methods=['POST'])
def delete_task():

    #the task itself has to be retrieved first
    #its done by finding and locating the id
    #in the task table
    task_id = request.form.get('task_id') 

    #if the task id is not returned, the user is flashed a message
    #this is because it cannot find a task without an id
    if not task_id:
        return "Task ID is required", 400

    #the task id is then retrieved from the Task table
    task = Task.query.get(task_id) 

    #the task id is then checked to see if the task is linked to the user table
    #if it's linked to the table, then the database is cleared of the task
    #the user is then messaged
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

    #the filter type is made a variable that equates to the user's choice
    filter_type = request.form.get('filter')

    query = Task.query.filter_by(user_id=current_user.id)

    #the filter types are listed below 
    #they work by using a query function related to the task
    #the tasks are then sorted in descending order
    #
    if filter_type == 'creation_date':
        query = query.order_by(Task.creation_date.desc())
    elif filter_type == 'due_date':
        today = date.today().isoformat()
        query = query.filter(func.strftime('%Y-%m-%d', Task.due_date) == today) 
    elif filter_type == 'completed':
        query = query.filter(Task.completed == True)
    elif filter_type == 'starred':
        query = query.filter(Task.starred == True)
    else:
        query = query.filter_by(user_id=current_user.id)

    tasks = query.all()

    return render_template('home.html', user=current_user, tasks=tasks)

#update task status function
@utils.route('update-task', methods=['POST'])
def update_task():

    #the last action performed on a task is taken into account
    task_id = request.form.get('task_id')
    action = request.form.get('action')
    task = Task.query.get(task_id)

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
        flash("Task not found or unable to be updated, try again!", category='error')

    return redirect(url_for('views.home'))

@utils.route('/reposition-task', methods=['POST'])
def reposition_task(user_id, task_id, direction):

    #user's current tasks retrieved
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()

    #if there are no tasks to move, the function outputs nothing
    if not task:
        return None

    #task list retrieved with the positions of each task having been established
    Tlist = Task.query.filter_by(user_id=user_id).order_by(Task.position).all()

    # Find the current task's position in the list
    index = Tlist.index(task)

    if direction == 'up' and index > 0:
        # Swap the task with the one above
        Tlist[index], Tlist[index - 1] = Tlist[index - 1], Tlist[index]
    elif direction == 'down' and index < len(Tlist) - 1:
        # Swap the task with the one below
        Tlist[index], Tlist[index + 1] = Tlist[index + 1], Tlist[index]

    # Update the position of each task
    for idx, t in enumerate(Tlist):
        t.position = idx
    db.session.commit()

    return task  # Return the task that was moved

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

    #message returned to tell the user the task order has been updatedd
    return jsonify({"message": "Your task order has updated!"}), 200
