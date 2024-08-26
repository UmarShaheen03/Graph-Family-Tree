from flask import Flask,  render_template, flash, redirect, url_for, request, session
from app import app

@app.route('/', methods = ['GET', 'POST'])
def landing():
    return render_template('landing.html')


if __name__=='__main__':
    app.run(debug=True)