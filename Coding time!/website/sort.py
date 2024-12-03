from flask import Blueprint, render_template, flash, redirect, url_for, request

from flask_login import login_required, current_user

from datetime import datetime

from . import db

from .models import Task, Preferences

sort = Blueprint('sort', __name__)

def normalize_tasks(tasks):

    max_due_date = max((task.due_date for task in tasks), default=datetime.utcnow())
    max_duration = max((task.duration for task in tasks), default=1)
    max_priority = max((int(task.priority) for task in tasks), default=1) 
    max_difficulty = max((int(task.difficulty) for task in tasks), default=1) 

    normalized_tasks = []
    for task in tasks:
        normalized_due = (1 - ((task.due_date - datetime.utcnow()).days / (max_due_date - datetime.utcnow()).days)) if task.due_date else 0
        normalized_duration = task.duration / max_duration
        normalized_priority = int(task.priority) / max_priority
        normalized_difficulty = int(task.difficulty) / max_difficulty

        normalized_tasks.append({
            "task": task,
            "due_date": normalized_due,
            "duration": normalized_duration,
            "priority": normalized_priority,
            "difficulty": normalized_difficulty
        })

    return normalized_tasks

def calculate_task_scores(tasks, preferences):
    normalized_tasks = normalize_tasks(tasks)

    weights = {
        "due_date": preferences.weight_due_date,
        "duration": preferences.weight_duration,
        "priority": preferences.weight_priority,
        "difficulty": preferences.weight_difficulty,
    }

    scored_tasks = []
    for task_data in normalized_tasks:
        task = task_data["task"]
        score = (
            weights["due_date"] * task_data["due_date"] +
            weights["duration"] * task_data["duration"] +
            weights["priority"] * task_data["priority"] +
            weights["difficulty"] * task_data["difficulty"]
        )
        scored_tasks.append((task, score))

    scored_tasks.sort(key=lambda x: x[1], reverse=True)
    return [task[0] for task in scored_tasks]

def adjust_weights(preferences, completed_tasks):
    overdue_tasks = [task for task in completed_tasks if task.due_date and task.due_date < datetime.utcnow()]
    long_tasks = [task for task in completed_tasks if task.duration > 4]

    if overdue_tasks:
        preferences.weight_due_date += 0.05
    if long_tasks:
        preferences.weight_duration -= 0.03

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

@sort.route('/sort-tasks', methods=['GET', 'POST'])
def sort_tasks():

    user_preferences = Preferences.query.filter_by(user_id=current_user.id).first()

    if not user_preferences:
        flash("Please set your preferences before sorting tasks.", category="warning")
        return redirect(url_for('views.home'))

    tasks_query = Task.query.filter_by(user_id=current_user.id).all()
    sorted_tasks = sorted(tasks_query, key=lambda task: task.duration)

    return render_template('home.html', user=current_user, tasks=sorted_tasks)