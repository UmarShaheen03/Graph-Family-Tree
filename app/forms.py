from flask_wtf import FlaskForm
from wtforms import EmailField, StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
import sqlalchemy as sa
from app import db
from app.models import User
from wtforms import TextAreaField
from wtforms.validators import Length
from flask_login import current_user

class LoginForm(FlaskForm):
    username_or_email = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Stay Logged In?')
    submit = SubmitField('Log In')


class SignupForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    repeat = PasswordField('Repeat Password',[DataRequired()])
    remember_me = BooleanField('Stay Logged In?')
    submit = SubmitField('Sign Up')


class AddNodeForm(FlaskForm):
    pass