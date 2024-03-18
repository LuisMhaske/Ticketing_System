from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from . import db, HRRegistrationForm
from forms import LoginForm
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if user.is_hr and user.is_approved:  # Check if user is an approved HR
                login_user(user)
                flash('Login successful.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('You are not authorized to log in.', 'danger')
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)
    # if request.method == 'POST':
    #     email = request.form.get('email')
    #     password = request.form.get('password')
    #     user = User.query.filter_by(email=email).first()
    #     if user and check_password_hash(user.password_hash, password):
    #         login_user(user)
    #         return redirect(url_for('index'))
    #     flash('Please check your login details and try again.')
    # return render_template('login.html')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists')
            return redirect(url_for('auth.signup'))
        new_user = User(email=email, password_hash=generate_password_hash(password, method='pbkdf2:sha256'))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('auth.login'))
    return render_template('registration.html')


