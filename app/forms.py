from flask_wtf import FlaskForm
from wtforms import EmailField, StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
#import sqlalchemy as sa
from app import db
from app.models import User
from wtforms import TextAreaField
from wtforms.validators import Length
from flask_login import current_user

class LoginForm(FlaskForm):
    ###


class RegistrationForm(FlaskForm):
    ####


class AddNodeForm(FlaskForm):
    ####


    