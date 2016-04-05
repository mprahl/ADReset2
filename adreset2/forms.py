"""
Author: StackFocus
File: forms.py
Purpose: form definitions for the app
"""

from flask_wtf import Form
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired
from adreset2.utils import validate_wtforms_password


class LoginForm(Form):
    """ Class for login form on /login
    """
    username = StringField(label='Username', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired(), validate_wtforms_password])
    auth_source = SelectField('PostMaster User', validators=[DataRequired()])

    @classmethod
    def new(cls):
        # Instantiate the form
        form = cls()
        # Set the default auth_source to local
        form.auth_source.choices = [('ADReset2 User', 'ADReset2 User')]

        return form
