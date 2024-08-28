"""Main route views"""

from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from app.forms import LoginForm, SignupForm
from app.accounts import signup, login, SignupError, LoginError

main_bp = Blueprint('main_bp', __name__)

@main_bp.route("/")
def home_page():
    """The landing page"""
    return render_template('home.html')

"""LOGIN AND SIGNUP PAGE/FORMS"""

@main_bp.route("/login")
def login_page():
    loginForm = LoginForm()
    return render_template("login.html", loginForm=loginForm)

@main_bp.route("/signup")
def signup_page():
    signupForm = SignupForm()
    return render_template("signup.html", signupForm=signupForm)

#form submissions for login
@main_bp.route("/login-form", methods=["POST"])
def login_request():
    form = LoginForm()

    #if form doesn't validate, redirect to signup page
    if not form.validate_on_submit():
        return login_page()
    
    email_or_username = request.form.get("email_or_username")
    password = request.form.get("password")
    remember = request.form.get("remember")

        #call function in other file
    try:
        login(email_or_username, password, remember)
    except LoginError as error:
        #TODO: display errors
        return login_page()
    
    #TODO: return route for main page

#form submissions for signup
@main_bp.route("/signup-form", methods=["POST"])
def signup_request():
    form = SignupForm()

    #if form doesn't validate, redirect to signup page
    if not form.validate_on_submit():
        return login_page()
    
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")
    repeat = request.form.get("repeat")

    #call function in other file
    try:
        signup(email, username, password, repeat)
    except SignupError as error:
        #TODO: display errors
        return login_page()
    
    #TODO: return route for main page

@main_bp.route("/tree")
def tree_page():
    """A family tree page"""
    return render_template('tree.html')

@main_bp.route("/biography")
def biography_page():
    """The biography page"""
    return render_template('biography.html')