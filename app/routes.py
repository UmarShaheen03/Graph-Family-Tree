from flask import Flask, render_template, flash, redirect, url_for, request, session
from app import app
from app.forms import LoginForm, SignupForm


#LOGIN AND SIGN UP ROUTES

#get requests for login page
@app.route("./login-signup", methods=["GET"])
def login_signup():
    loginForm = LoginForm()
    signupForm = SignupForm()
    return render_template("login_signup.html", title="Login or Sign Up", loginForm=loginForm, signupForm=signupForm, redirect=redirect)

#form submissions for signup
@app.route("./signup-form", methods=["POST"])
def login_signup():
    form = SignupForm()

    #if form doesn't validate, redirect to signup page
    if not form.validate_on_submit():
        return login_signup()
    
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")
    repeat = request.form.get("repeat")
    
#form submissions for signup
@app.route("./login-form", methods=["POST"])
def login_signup():
    form = LoginForm()

    #if form doesn't validate, redirect to signup page
    if not form.validate_on_submit():
        return login_signup()
    
    username = request.form.get("username")
    password = request.form.get("password")
    repeat = request.form.get("repeat")