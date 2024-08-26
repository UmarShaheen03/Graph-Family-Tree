from flask_wtf import FlaskForm
from wtforms import EmailField, StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
import sqlalchemy as sa
#from app import db
#from app.models import User
from wtforms import TextAreaField
from wtforms.validators import Length
from flask_login import current_user

class LoginForm(FlaskForm):
   pass


class SignupForm(FlaskForm):
    pass


class AddNodeForm(FlaskForm):
    ####
    action = SelectField(
        'Action', 
        choices=[('create', 'Create'), ('update', 'Update'), ('delete', 'Delete')],
        validators=[DataRequired()]
    )
    
    name = StringField(
        'Name', 
        validators=[DataRequired()]
    )
    
    parent = SelectField(
        'Parent', 
        choices=[],  # You will populate this dynamically in your view or route
        validators=[DataRequired()]
    )
    
    submit = SubmitField('Submit')