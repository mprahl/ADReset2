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


class Configs(db.Model):
    """ Table to store configuration items
    """

    __tablename__ = 'adreset2_configuration'
    id = db.Column(db.Integer, primary_key=True)
    setting = db.Column(db.String(128), unique=True)
    value = db.Column(db.String(512))
    regex = db.Column(db.String(256))

    def to_json(self):
        """ Returns the database row in JSON
        """
        rv = {'id': self.id, 'setting': self.setting, 'regex': self.regex}
        if self.setting == 'AD Service Account Password' and self.value:
            rv['value'] = 'set'
        else:
            rv['value'] = self.value
        return rv

    def from_json(self, json):
        """ Returns a database row from JSON input
        """
        if not json.get('setting', None):
            raise ValidationError('The setting was not specified')
        if not json.get('value', None):
            raise ValidationError('The value of the setting was not specified')
        if not json.get('regex', None):
            raise ValidationError('The regex for valid setting values was not specified')
        if self.query.filter_by(setting=json['setting']).first() is not None:
            raise ValidationError('The setting "{0}" already exists'.format(
                json['setting']))
        self.setting = json['setting']
        self.value = json['value']
        self.regex = json['regex']
        return self


class AdConfigs(db.Model):
    """ Table to store AD configuration items
    """

    __tablename__ = 'adreset2_ad_configuration'
    id = db.Column(db.Integer, primary_key=True)
    setting = db.Column(db.String(128), unique=True)
    value = db.Column(db.String(512))

    def to_json(self):
        """ Returns the database row in JSON
        """
        rv = {'id': self.id, 'setting': self.setting, 'regex': self.regex}
        if self.setting == 'AD Service Account Password' and self.value:
            rv['value'] = 'set'
        else:
            rv['value'] = self.value
        return rv

    def from_json(self, json):
        """ Returns a database row from JSON input
        """
        if not json.get('setting', None):
            raise ValidationError('The setting was not specified')
        if not json.get('value', None):
            raise ValidationError('The value of the setting was not specified')
        if self.query.filter_by(setting=json['setting']).first() is not None:
            raise ValidationError('The setting "{0}" already exists'.format(
                json['setting']))
        self.setting = json['setting']
        self.value = json['value']
        return self
