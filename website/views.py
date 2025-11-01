from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from Scraper import Scraper
from .models import get_tasks_details, get_user_cookies

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
    result = scraper.run_scraper(current_user.id, month_year)
    
    if result:
        flash('Scraping completed successfully!', category='success')
        return redirect(url_for('views.home'))
    else:
        flash('Your session has timed out. Please log in again.', category='danger')
        return redirect(url_for('auth.login'))
    
@views.route('/shutdown')
def shutdown():
    """Shutdown the server"""
    flash('Server is shutting down...', category='info')
    import threading, os
    threading.Timer(1, lambda: os._exit(0)).start()
    return redirect(url_for('auth.login'))