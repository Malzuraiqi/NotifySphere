from . import db
from flask_login import UserMixin
import json

class User(db.Model, UserMixin):
    """User model for authentication and storing Moodle session"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    moodle_cookies = db.Column(db.Text)
    tasks = db.relationship('Task', backref='user', lazy=True)

class Task(db.Model):
    """Task model for storing assignment details with user relationship"""
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer)
    month = db.Column(db.String(50))  # Changed to String to match your timestamp format
    course = db.Column(db.String(255))
    assignment = db.Column(db.String(255))
    status = db.Column(db.String(100))
    due_date = db.Column(db.String(100))
    url = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Unique constraint per user
    __table_args__ = (db.UniqueConstraint('user_id', 'course', 'assignment', name='_user_course_assignment_uc'),)

def get_user_cookies(user_id):
    """Retrieve saved Moodle cookies for a user from database"""
    user = User.query.get(user_id)
    if user and user.moodle_cookies:
        return json.loads(user.moodle_cookies)
    return None

def save_user_cookies(user_id, cookies):
    """Save Moodle session cookies to database for persistent login"""
    user = User.query.get(user_id)
    if user:
        user.moodle_cookies = json.dumps(cookies)
        db.session.commit()

def insert_tasks(user_id, tasks_details):
    """Insert or update tasks for a user, handling duplicates via unique constraint"""
    for task in tasks_details:
        task_data = {
            'user_id': user_id,
            'day': task.get('day'),
            'month': task.get('month'),
            'course': task.get('course'),
            'assignment': task.get('assignment'),
            'status': task.get('status'),
            'due_date': task.get('due_date'),
            'url': task.get('url')
        }
        
        # Check if task already exists
        existing_task = Task.query.filter_by(
            user_id=user_id,
            course=task_data['course'],
            assignment=task_data['assignment']
        ).first()
        
        if existing_task:
            # Update existing task
            existing_task.day = task_data['day']
            existing_task.month = task_data['month']
            existing_task.status = task_data['status']
            existing_task.due_date = task_data['due_date']
            existing_task.url = task_data['url']
        else:
            # Insert new task
            new_task = Task(**task_data)
            db.session.add(new_task)
    
    db.session.commit()

def get_tasks_details(user_id):
    """Retrieve all tasks for a user sorted by deadline (nearest first)"""
    tasks = Task.query.filter_by(user_id=user_id)\
        .order_by(Task.month.desc(), Task.day.desc())\
        .all()
    return [{
        'day': task.day,
        'month': task.month,
        'course': task.course,
        'assignment': task.assignment,
        'status': task.status,
        'due_date': task.due_date,
        'url': task.url
    } for task in tasks]

def get_tasks_for_comparison(user_id):
    """Get submitted tasks for comparison during scraping to avoid scarping again"""
    tasks = Task.query.filter_by(user_id=user_id, status='Submitted for grading').all()
    return [(task.day, task.assignment) for task in tasks]