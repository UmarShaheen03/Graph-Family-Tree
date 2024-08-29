from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

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
