import sqlalchemy as sa
from app.models import User
from flask_login import current_user
from flask import Flask, flash, render_template, redirect, request, session, url_for
from wtforms import EmailField, FieldList, FileField, FormField, SelectField, SelectMultipleField, StringField, DateField, IntegerField, PasswordField, TextAreaField, SubmitField, BooleanField, widgets
from wtforms.validators import DataRequired, NumberRange, Email, ValidationError, EqualTo, Length, Optional
from flask_wtf import CSRFProtect, FlaskForm

class LoginForm(FlaskForm):
    username_or_email = StringField("Username or Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Stay logged in?")
    submit = SubmitField("Log In")

class LogoutForm(FlaskForm):
    submit = SubmitField("Log Out")
    
class SignupForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    repeat = PasswordField("Repeat Password", validators=[DataRequired()])
    remember_me = BooleanField("Stay logged in?")
    submit = SubmitField("Sign Up")

class ForgotPassword(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Submit")

class ResetPassword(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    repeat = PasswordField("Repeat Password", validators=[DataRequired()])
    submit = SubmitField("Reset")



class AddNodeForm(FlaskForm):

    action = SelectField(
        'Action',
        choices=[
            ('add', 'Add Person'),
            ('edit', 'Edit Person'),
            ('delete', 'Delete Person'),
            ('shift', 'Shift Person')
        ]
    )

    name = StringField(
        'Name',
        render_kw={"placeholder": "Enter name"}  # Only shown when 'Add Person' or 'Edit Person' is selected
    )

    new_name = StringField(
        'New Name',
        render_kw={"placeholder": "Enter new name"}  # Only shown when 'Add Person' or 'Edit Person' is selected
    )

    person_to_shift = SelectField(
        'Person to Shift',
        choices=[]  # Populate this dynamically in your view
    )
    person_to_delete = SelectField(
        'Person to Delete',
        choices=[]  # Populate this dynamically in your view
    )

    old_name = SelectField(
        'Old Name',
        choices=[]  # Populate this dynamically in your view
    )

    parent = SelectField(
        'Parent',
        choices=[]  # Populate this dynamically in your view
    )

    new_parent = SelectField(
        'New Parent',
        choices=[]  # Populate this dynamically in your view
    )

    submit = SubmitField('Submit')

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

class CommentForm(FlaskForm):
    comment=TextAreaField('Comment', validators=[DataRequired()])
    submit=SubmitField('Submit')

class BiographyEditForm(FlaskForm):
    fullname = SelectField(
        'Full Name',
        choices=[]  # Populate this dynamically in your view
    )
    dob=DateField('Date of Birth', validators=[Optional()])
    biography=StringField('Biography', validators=[Optional()])
    location=StringField('Location', validators=[Optional()])
    email=EmailField('Email', validators=[Optional()])
    phonenumber=IntegerField('Phone Number', validators=[Optional()])
    address=StringField('Address', validators=[Optional()])
    submit=SubmitField('Update')

class Search_Node (FlaskForm):
      fullname = SelectField(
        'Search',
        choices=[]  # Populate this dynamically in your view
    )
      submit = SubmitField("Search")


class submit_File (FlaskForm):
    file=FileField("Upload Your CSV file")
    name=StringField("Name of the tree")
    submit=SubmitField('Submit')


class Request_Tree (FlaskForm):
    tree_name = SelectField(
        'Select Tree Name',
        choices=[]  # Populate this dynamically in your view
    )
    submit = SubmitField("Submit")


class RequestTreeForm(FlaskForm):
    tree_name = SelectField(
        choices=[],  # This can be populated dynamically in your view
        validators=[DataRequired()],
        render_kw={"class": "form-control rounded-pill"}
    )
   
    submit = SubmitField('Submit Request', render_kw={"class": "btn btn-primary rounded-pill"})

class EmailPreference(FlaskForm):
    preference = SelectField(
        "Choose how often would you like emails, and submit (emails are sent 5pm daily, or 5pm Friday if weekly).",
        choices=["Daily","Weekly","None"],
        validators=[DataRequired()]
    )
    submit=SubmitField("Submit Preferences")

class IgnoreNotifs (FlaskForm):
    login=BooleanField("Logins", default=False)
    logout=BooleanField("Logouts", default=False)
    reset=BooleanField("Password Resets", default=False)
    signup=BooleanField("Sign Ups", default=False)

    admin_req=BooleanField("Admin Requests", default=False)
    tree_req=BooleanField("Tree Requests", default=False)
    req_accepted=BooleanField("Request Accept", default=False)

    comment=BooleanField("New Comments", default=False)
    bio_edit=BooleanField("Biography Edits", default=False)

    new_tree=BooleanField("New Tree", default=False)
    tree_create=BooleanField("New Person", default=False)
    tree_move=BooleanField("Person Moved", default=False)
    tree_update=BooleanField("Person Renamed", default=False)
    tree_delete=BooleanField("Person Removed", default=False)

    submit=SubmitField("Submit Preferences")
    # "Login", "Logout", "Reset", "Signup" (account related) 
    # "Admin Request", "Tree Request", "Request" (request related)
    # "Comment", "Bio Edit" (bio related)
    # "New Tree", "Tree Create", "Tree Move", "Tree Update" "Tree Delete" (tree related)