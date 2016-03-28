"""
Author: StackFocus
File: models.py
Purpose: contains the models of the application's database
"""

from adreset2 import db, bcrypt
from adreset2.errors import ValidationError


class Admins(db.Model):
    """ A table to store the admin users
    """
    __tablename__ = 'adreset2_admins'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(64))
    source = db.Column(db.String(64))
    active = db.Column(db.Boolean, default=True)

    def is_active(self):
        """ Returns if user is active
        """
        return self.active

    def get_id(self):
        """ Returns id of user
        """
        return self.id

    def is_authenticated(self):
        """ Returns if user is authenticated. This is hooked by flask-login.
        """
        return True

    def is_anonymous(self):
        """ Returns if guest
        """
        # Anonymous users are not supported
        return False

    def __repr__(self):
        return '<adreset2_admins(username=\'{0}\')>'.format(self.username)

    def to_json(self):
        """ Returns a dictionary of the user while leaving the password out
        """
        return {'id': self.id, 'name': self.name, 'username': self.username}

    def from_json(self, json):
        if not json.get('username', None):
            raise ValidationError('The username was not specified')
        if not json.get('password', None):
            raise ValidationError('The password was not specified')
        if not json.get('name', None):
            raise ValidationError('The name was not specified')
        if self.query.filter_by(username=json['username']).first() is not None:
            raise ValidationError('"{0}" already exists'.format(
                json['username'].lower()))
        self.password = bcrypt.generate_password_hash(json['password'])
        self.username = json['username'].lower()
        self.name = json['name']
        self.source = 'local'
        self.active = True
        return self
