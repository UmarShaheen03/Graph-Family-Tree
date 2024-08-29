from flask_wtf import FlaskForm
from wtforms import EmailField, StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
import sqlalchemy as sa
from app import db
from app.models import User
from wtforms import TextAreaField
from wtforms.validators import Length
from flask_login import current_user
from flask import Flask, flash, render_template, redirect, request, session, url_for
from flask_wtf import CSRFProtect, FlaskForm
from wtforms import EmailField, FieldList, FormField, SelectField, SelectMultipleField, StringField, DateField, IntegerField, TextAreaField, SubmitField, widgets
from wtforms.validators import DataRequired, NumberRange, email


    
class LoginForm(FlaskForm):
    ###


class RegistrationForm(FlaskForm):
    ####


class AddNodeForm(FlaskForm):
    ####

