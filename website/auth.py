from flask import Blueprint, render_template, request, url_for, flash, redirect
import requests
from flask_login import login_user, current_user, logout_user
from .models import User, save_user_cookies
from . import db
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

auth = Blueprint('auth', __name__)

LOGIN_URL = "https://my.cud.ac.ae/login/index.php"
TARGET_URL = "https://my.cud.ac.ae/my/"

def get_cookies_during_login(username, password):
    session = requests.Session()

    r = session.get(TARGET_URL, verify=False)

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r.text, 'html.parser')
    token_input = soup.find("input", {"name": "logintoken"})
    token = token_input['value'] if token_input else ""

    payload = {
        "username": username,
        "password": password,
        "logintoken": token
    }
    r = session.post(LOGIN_URL, data=payload, verify=False)

    if "my.cud.ac.ae/my/" in r.url and session.cookies:
        cookies_list = [
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path,
                "secure": c.secure,
                "httpOnly": False,
                "sameSite": "Lax"
            }
            for c in session.cookies
        ]
        print(cookies_list)
        return cookies_list
    else:
        print("login failed or no cookies")
        return None

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