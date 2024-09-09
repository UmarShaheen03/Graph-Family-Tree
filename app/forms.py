from flask_wtf import FlaskForm
from wtforms import EmailField, StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Optional
import sqlalchemy as sa
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
class CommentForm(FlaskForm):
    comment=TextAreaField('Comment', validators=[DataRequired()])
    submit=SubmitField('Submit')

class BiographyEditForm(FlaskForm):
    name=StringField('Full Name', validators=[DataRequired()])
    dob =StringField('Date of Birth', validators=[Optional()])
    biography=StringField('Biography', validators=[Optional()])
    location=StringField('Location', validators=[Optional()])
    email=StringField('Email', validators=[Optional()])
    phonenumber=StringField('Phone Number', validators=[Optional()])
    address=StringField('Address', validators=[Optional()])
    submit=SubmitField