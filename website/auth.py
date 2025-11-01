from flask import Blueprint, render_template, request, url_for, flash, redirect
import re
from playwright.sync_api import sync_playwright
from flask_login import login_user, current_user, logout_user
from .models import User, save_user_cookies
from . import db
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

auth = Blueprint('auth', __name__)

"""
def get_cookies_during_login(username, password):
    # Attempt login and return cookies if successful
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://my.cud.ac.ae/my/")
        page.fill('#username', username)
        page.fill('#password', password)
        page.click('button[type="submit"]')
        page.wait_for_url(re.compile(r".*my\.cud\.ac\.ae.*"))
        
        if 'https://my.cud.ac.ae/my/' in page.url:
            cookies = context.cookies()
            context.close()
            browser.close()
            return cookies
        else:
            context.close()
            browser.close()
            return None
"""

def get_cookies_during_login(username, password):
    """Attempt login and return cookies if successful"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get("https://my.cud.ac.ae/my/")
        
        # Fill login form
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        submit_button.click()
        
        # Wait for navigation
        WebDriverWait(driver, 10).until(EC.url_contains("my.cud.ac.ae"))
        
        # Check if login successful
        if 'https://my.cud.ac.ae/my/' in driver.current_url:
            cookies = driver.get_cookies()
            
            # Also try to get cookies from the other domain
            driver.get("https://yourvoice.cud.ac.ae/")
            yourvoice_cookies = driver.get_cookies()
            
            all_cookies = yourvoice_cookies + cookies
            return all_cookies
        else:
            return None
            
    except Exception as e:
        print(f"Login error: {e}")
        return None
    finally:
        driver.quit()

@auth.route('/login', methods=['POST', 'GET'])
def login():
    """Handle user login with Moodle credentials"""
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Please enter both email and password', category='warrning')
            return render_template('login.html', user=current_user)

        cookies = get_cookies_during_login(username, password)
        
        if cookies:
            user = User.query.filter_by(email=username).first()
            if not user:
                user = User(email=username)
                db.session.add(user)
                db.session.commit()
            
            login_user(user, remember=True)
            save_user_cookies(user.id, cookies)
            flash('Logged in successfully', category='success')
            return redirect(url_for('views.home'))
        else:
            flash('Incorrect email or password', category='danger')
        
    return render_template('login.html', user=current_user)
    
@auth.route('/logout')
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out', category='info')
    return redirect(url_for('auth.login'))