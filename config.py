"""
Author: StackFocus
File: config.py
Purpose: config for the app
"""

from os import path


class BaseConfiguration(object):
    # We disable CSRF because it interferes with logging in
    # from anywhere but the form on the login page.
    # We introduce very little risk by disabling this.
    WTF_CSRF_ENABLED = False
    # Make this random (used to generate session keys)
    SECRET_KEY = '4d4663c6cddb4bcd3eeca2f19e03ea3479d4fc3390ada0a4'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    BASE_DIR = path.abspath(path.dirname(__file__))
    DB_DIR = path.join(BASE_DIR, 'db')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + path.join(DB_DIR, 'adreset2.db')


class TestConfiguration(BaseConfiguration):
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    DEBUG = True
