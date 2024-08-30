from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
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



class RelationshipForm(FlaskForm):
    node = SelectField('Node:', choices=[], validators=[DataRequired()])
    relationship_type = StringField('Relationship Type:')

class UpdateNode (FlaskForm):
    Nodes = SelectField(
        'Select Node:',
        choices=[],  # Will be populated dynamically
        widget=widgets.ListWidget(prefix_label=False),
        option_widget=widgets.RadioInput()  # Use radio buttons for single choice
    )
    FullName = StringField("Full Name:")
    DateOfBirth = DateField("Date of Birth")
    Age = IntegerField("Age")
    About = TextAreaField("About",)
    Location = TextAreaField("General Comments")
    Email = EmailField("Email")
    PhoneNumber = IntegerField("PhoneNumber",validators=[NumberRange(min=1000000000, max=9999999999)])
    Address = StringField("Address")  # Added correct form type
    node_choices = SelectMultipleField('Select Nodes:', choices=[], option_widget=widgets.CheckboxInput(), widget=widgets.ListWidget(prefix_label=False))
    relationship_type= StringField("Address")
    relationships = FieldList(FormField(RelationshipForm), min_entries=1, max_entries=10) 
    submit = SubmitField("Add to Family Tree")


    
class AppendGraph(FlaskForm):
    FullName = StringField("Full Name:")
    DateOfBirth = DateField("Date of Birth")
    Age = IntegerField("Age")
    About = TextAreaField("About",)
    Location = TextAreaField("General Comments")
    Email = EmailField("Email")
    PhoneNumber = IntegerField("PhoneNumber")
    Address = StringField("Address")  # Added correct form type
    node_choices = SelectMultipleField('Connect to Node:', choices=[], option_widget=widgets.CheckboxInput(), widget=widgets.ListWidget(prefix_label=False))
    relationship_type= StringField("Address")
    relationships = FieldList(FormField(RelationshipForm), min_entries=1, max_entries=10) 
    submit = SubmitField("Add to Family Tree")




    
class LoginForm(FlaskForm):
    ###


class RegistrationForm(FlaskForm):
    ####


class AddNodeForm(FlaskForm):
    action = SelectField(
        'Action', 
        choices=[('add', 'Add Person'), ('edit', 'Edit Person'), ('delete', 'Delete Person'), ('shift', 'Shift Person')],
        validators=[DataRequired()]
    )
    
    name = StringField(
        'Name', 
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter name"}  # Only shown when 'Add Person' or 'Edit Person' is selected
    )
    new_name = StringField(
        'New Name', 
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter new name"}  # Only shown when 'Add Person' or 'Edit Person' is selected
    )
    person_to_shift = SelectField(
        'Person to Shift', 
        choices=[],  # Populate this dynamically in your view
        validators=[DataRequired()]
    )
    person_to_delete = SelectField(
        'Person to Delete', 
        choices=[],  # Populate this dynamically in your view
        validators=[DataRequired()]
    )
    old_name = SelectField(
        'Old Name', 
        choices=[],  # Populate this dynamically in your view
        validators=[DataRequired()]
    )
    
    parent = SelectField(
        'Parent', 
        choices=[],  # Populate this dynamically in your view
        validators=[DataRequired()]
    )
    
    new_parent = SelectField(
        'New Parent', 
        choices=[],  # Populate this dynamically in your view
        validators=[DataRequired()]
    )
    
    submit = SubmitField('Submit')

    ####

