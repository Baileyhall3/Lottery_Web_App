# IMPORTS
import logging
from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import db, requires_roles
from models import User
from users.forms import RegisterForm, LoginForm
import pyotp

# CONFIG
users_blueprint = Blueprint('users', __name__, template_folder='templates')


# VIEWS
# view registration
@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # create signup form object
    form = RegisterForm()

    # if request method is POST or form is valid
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # if this returns a user, then the email already exists in database

        # if email already exists redirect user back to signup page with error message so user can try again
        if user:
            flash('Email address already exists')
            return render_template('register.html', form=form)

        # create a new user with the form data
        new_user = User(email=form.email.data,
                        firstname=form.firstname.data,
                        lastname=form.lastname.data,
                        phone=form.phone.data,
                        password=form.password.data,
                        pin_key=form.pin_key.data,
                        role='user')

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        # Logs user registration to security log file
        logging.warning('SECURITY - User registration [%s, %s]', form.email.data, request.remote_addr)

        # sends user to login page
        return redirect(url_for('users.login'))
    # if request method is GET or form not valid re-render signup page
    return render_template('register.html', form=form)


# view user login
@users_blueprint.route('/user.login', methods=['GET', 'POST'])
def login():

    # if session attribute logins does not exist create attribute logins
    if not session.get('logins'):
        session['logins'] = 0
    # if login attempts are equal to or greater than 3, display error message
    elif session.get('logins') >= 3:
        flash('Number of incorrect logins exceeded')

    form = LoginForm()

    if form.validate_on_submit():

        # increases login attempts by 1
        session['logins'] += 1

        user = User.query.filter_by(email=form.username.data).first()

        if not user or not check_password_hash(user.password, form.password.data):

            # if the passwords do not match, display an error message based on number of login attempts
            if session['logins'] == 3:
                logging.warning('SECURITY - Invalid login [%s, %s]', form.username.data, request.remote_addr)
                flash('Number of incorrect logins exceeded')
            elif session['logins'] == 2:
                logging.warning('SECURITY - Invalid login [%s, %s]', form.username.data, request.remote_addr)
                flash('Please check your login details and try again. 1 attempt remaining')
            else:
                logging.warning('SECURITY - Invalid login [%s, %s]', form.username.data, request.remote_addr)
                flash('Please check your login details and try again. 2 attempts remaining')

            return render_template('login.html', form=form)

        if pyotp.TOTP(user.pin_key).verify(form.pin.data):

            # if user is verified reset the login attempts to 0
            session['logins'] = 0

            login_user(user)

            # Collects data from users logging in to add to DB
            user.last_logged_in = user.current_logged_in
            user.current_logged_in = datetime.now()
            db.session.add(user)
            db.session.commit()

            #logs a user logging into the system
            logging.warning('SECURITY - Log in [%s, %s, %s]', current_user.id,
                            current_user.email, request.remote_addr)

            #direct to appropriate page
            if current_user.role == 'user':
                return profile()
            else:
                return redirect(url_for('admin.admin'))

        else:
            flash("Invalid 2FA token supplied", "danger")

    return render_template('login.html', form=form)


# LOGOUT page view
@users_blueprint.route('/logout')
@login_required
def logout():

    #Logs the user logging out to lottery.log
    logging.warning('SECURITY - Log out [%s, %s, %s]', current_user.id,
                    current_user.email, request.remote_addr)
    logout_user()
    return redirect(url_for('index'))


# view user profile
@users_blueprint.route('/profile')
@login_required
@requires_roles('user')
def profile():
    return render_template('profile.html', name=current_user.firstname)


# view user account
@users_blueprint.route('/account')
@login_required
def account():
    return render_template('account.html',
                           acc_no=current_user.id,
                           email=current_user.email,
                           firstname=current_user.firstname,
                           lastname=current_user.lastname,
                           phone=current_user.phone)
