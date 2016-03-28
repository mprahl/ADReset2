"""
Author: StackFocus
File: views.py
Purpose: contains the views of the application
"""

from flask import render_template, redirect, request
from adreset2 import app, login_manager, models


@login_manager.user_loader
def user_loader(user_id):
    """ Function to return user for login
    """
    return models.Admins.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized_callback():
    """ Function to redirect after logging in when prompted for login
    """
    return redirect('/login?next=' + request.path)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')
