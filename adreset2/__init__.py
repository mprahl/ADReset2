"""
Author: StackFocus
File: __init__.py
Purpose: initializes the application
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object('config.BaseConfiguration')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)

from adreset2 import views, models
