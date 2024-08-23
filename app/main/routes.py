from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from app.forms import LoginForm, SignupForm
from app.accounts import signup, login, SignupError, LoginError

main_bp = Blueprint('main_bp', __name__)

#LOGIN AND SIGN UP ROUTES

@main_bp.route("/")
def route_login_signup():
    loginForm = LoginForm()
    signupForm = SignupForm()
    return render_template("login.html", loginForm=loginForm, signupForm=signupForm)

#form submissions for signup
@main_bp.route("/signup-form", methods=["POST"])
def signup_request():
    form = SignupForm()

    #if form doesn't validate, redirect to signup page
    if not form.validate_on_submit():
        return route_login_signup()
    
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")
    repeat = request.form.get("repeat")

    #call function in other file
    try:
        signup(email, username, password, repeat)
    except SignupError as error:
        #TODO: display errors
        return route_login_signup()
    
    #TODO: return route for main page
    
#form submissions for signup
@main_bp.route("/login-form", methods=["POST"])
def login_request():
    form = LoginForm()

    #if form doesn't validate, redirect to signup page
    if not form.validate_on_submit():
        return route_login_signup()
    
    email_or_username = request.form.get("email_or_username")
    password = request.form.get("password")
    remember = request.form.get("remember")

        #call function in other file
    try:
        login(email_or_username, password, remember)
    except LoginError as error:
        #TODO: display errors
        return route_login_signup()
    
    #TODO: return route for main page