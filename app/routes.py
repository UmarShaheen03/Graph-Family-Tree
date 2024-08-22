from flask import Flask, render_template, flash, redirect, url_for, request, session
from app import app
from app.forms import LoginForm, SignupForm
from accounts import signup, login, SignupError, LoginError


#LOGIN AND SIGN UP ROUTES

@app.route("/login")
def route_login_signup():
    loginForm = LoginForm()
    signupForm = SignupForm()
    return render_template("login_signup.html", loginForm=loginForm, signupForm=signupForm)

#form submissions for signup
@app.route("/signup-form", methods=["POST"])
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
        print(error)
        return route_login_signup()
    
    #return route for main page
    
#form submissions for signup
@app.route("/login-form", methods=["POST"])
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
        print(error)
        return route_login_signup()
    
    #return route for main page