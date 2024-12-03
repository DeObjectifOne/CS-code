from flask import Blueprint, render_template, request, flash, redirect, url_for

from . import db

from .models import User, Task

from flask_login import login_required, current_user

from datetime import datetime

utils = Blueprint('utils', __name__)

@utils.route('/creation', methods=['GET', 'POST'])
@login_required
def create_task():
    try:
        if request.method == 'POST':
            details = request.form.get("details")
            duration = float(request.form.get('duration', 0))
            due_date_str = request.form.get("due_date")

            priority_map = {"Low": 3, "Medium": 2, "High": 1}
            difficulty_map = {"Easy": 1, "Medium": 2, "Hard": 3}

            priority = priority_map.get(request.form.get('priority'), 1)  
            difficulty = difficulty_map.get(request.form.get('difficulty'), 1)  
            due_date = datetime.fromisoformat(due_date_str)

            if not details:
                flash("Task details are required", category='error')
            else:
                new_task = Task(
                    details=details,
                    duration=duration,
                    due_date=due_date,
                    priority=priority,
                    difficulty=difficulty,
                    user_id=current_user.id
                )
                db.session.add(new_task)
                db.session.commit()
                flash("Task created successfully", category='success')
                return redirect(url_for('views.home'))
    
    except ValueError:
        flash("Invalid input, try again", category="error")
        return redirect(url_for('utils.create_task'))

    return render_template('creation.html', user=current_user)

@utils.route('/edit-task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):

    task = Task.query.get_or_404(task_id)
    
    if task.user_id != current_user.id:
        flash("You are not authorized to edit this task.", category="error")
        return redirect(url_for('views.home'))
    
    if request.method == 'POST':
        task.details = request.form.get('details')
        task.duration = float(request.form.get('duration', 0))
        task.due_date = request.form.get('due_date')

        priority_map = {"Low": 3, "Medium": 2, "High": 1}
        difficulty_map = {"Easy": 1, "Medium": 2, "Hard": 3}
        
        if task.due_date:
            try:
                task.due_date = datetime.fromisoformat(task.due_date)
            except ValueError:
                flash("Invalid date format. Please try again.", category="error")
                return redirect(url_for('utils.edit_task', task_id=task_id))
        
        task.priority = priority_map.get(request.form.get('priority'), 1)
        task.difficulty = difficulty_map.get(request.form.get('difficulty'), 1)

        db.session.commit()
        flash("Task updated successfully!", category="success")
        return redirect(url_for('views.home'))
    
    return render_template('editing.html', task=task)


@utils.route('/delete-task', methods=['POST'])
def delete_task():
    task_id = request.form.get('task_id') 

    if not task_id:
        return "Task ID is required", 400

    task = Task.query.get(task_id) 

    if task and task.user_id == current_user.id:  
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted successfully!", category="success")
        return redirect(url_for('views.home'))

    flash("Task not found or you don't have permission to delete it.", category="error")
    return redirect(url_for('views.home'))

@utils.route('/filter', methods=['GET', 'POST'])
def filter_tasks():
    filter_type = request.form.get('filter')

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

    return render_template('home.html', user=current_user, tasks=tasks)

@utils.route('update-task', methods=['POST'])
def update_task():
    task_id = request.form.get('task_id')
    action = request.form.get('action')
    task = Task.query.get(task_id)

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
