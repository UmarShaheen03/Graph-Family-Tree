"""Main route views"""

from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from app.forms import LoginForm, SignupForm, ForgotPassword
from app.accounts import signup, login, SignupError, LoginError, init_database


main_bp = Blueprint('main_bp', __name__)

#test function, resets database and adds two mock users
@main_bp.before_request
def run_once_on_start():
    init_database()
    #replaces code of this function with none, so it only runs once
    run_once_on_start.__code__ = (lambda:None).__code__

@main_bp.route("/")
def home_page():
    """The landing page"""
    return render_template('home.html')

"""LOGIN AND SIGNUP PAGE/FORMS"""

@main_bp.route("/login")
def login_page():
    loginForm = LoginForm()
    return render_template("login.html", loginForm=loginForm, error="")

@main_bp.route("/signup")
def signup_page():
    signupForm = SignupForm()
    return render_template("signup.html", signupForm=signupForm, error="")

#form submissions for login
@main_bp.route("/login-form", methods=["POST"])
def login_request():
    form = LoginForm()

    #form validation isn't working, so commented out
    #TODO: figure out why it isn't validating
    #if not form.validate_on_submit():
    #    return render_template("login.html", loginForm=form, error="Invalid form")
    
    username_or_email = request.form.get("username_or_email")
    password = request.form.get("password")
    remember = request.form.get("remember")

    #call login function from other file
    try:
        login(username_or_email, password, remember)
    except LoginError as error:
        return render_template("login.html", loginForm=form, error=error)

    #currently sends to home page on success
    return home_page()

#form submissions for signup
@main_bp.route("/signup-form", methods=["POST"])
def signup_request():
    form = SignupForm()

    #form validation isn't working, so commented out
    #TODO: figure out why it isn't validating
    #if not form.validate_on_submit():
    #    return render_template("signup.html", signupForm=form, error="Invalid form")
    
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")
    repeat = request.form.get("repeat")
    remember = request.form.get("remember")

    #call signup function from other file
    try:
        signup(email, username, password, repeat, remember)
    except SignupError as error:
        return render_template("signup.html", signupForm=form, error=error)
    
    #currently sends to home page on success
    return home_page()

@main_bp.route("/forgot")
def forgot_password_page():
    form = ForgotPassword()
    return render_template("forgot.html", forgotForm=form, submitted=False)

@main_bp.route("/forgot-form", methods=["POST"])
def forgot_request():
    form = ForgotPassword()
    return render_template("forgot.html", forgotForm=form, submitted=True)



@main_bp.route("/tree")
def tree_page():
    """A family tree page"""
    return render_template('tree.html')

@main_bp.route("/biography")
def biography_page():
    """The biography page"""
    return render_template('biography.html')