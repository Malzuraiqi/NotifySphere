from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from Scraper import Scraper
from .models import get_tasks_details, insert_tasks

"""Blueprint for main application views and routes"""
views = Blueprint('views', __name__)

@views.route('/')
@login_required
def home():
    """Dashboard page displaying user's assignments and tasks"""
    try:
        assignments = get_tasks_details(current_user.id)
        return render_template('home.html', user=current_user, assignments=assignments)
    except Exception as e:
        flash('Error loading assignments', category='danger')
        return render_template('home.html', user=current_user, assignments=[])
    
@views.route('/start-scraping', methods=['POST'])
@login_required
def start_scraping():
    """Initiate scraping process for selected month and handle session expiry"""
    month_year = request.form.get('month_year')
    if not month_year:
        flash('Please select a month', category='warning')
        return redirect(url_for('views.home'))

    scraper = Scraper()

    # Step 1: Initialize session with cookies
    if not scraper.init_session_with_cookies(current_user.id):
        flash('Your session has timed out. Please log in again.', category='danger')
        return redirect(url_for('auth.login'))

    # Step 2: Get tasks for the month
    tasks = scraper.get_tasks(month_year, current_user.id)

    # Step 3: Insert new tasks into the database
    insert_tasks(current_user.id, tasks)

    flash('Scraping completed successfully!', category='success')
    return redirect(url_for('views.home'))

    
@views.route('/shutdown')
def shutdown():
    """Shutdown the server"""
    flash('Server is shutting down...', category='info')
    import threading, os
    threading.Timer(1, lambda: os._exit(0)).start()
    return redirect(url_for('auth.login'))