# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

import os.path
from datetime import timedelta

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))


class Config(object):
    """The base ADReset application configuration."""

    DEBUG = True
    # We configure logging explicitly, turn off the Flask-supplied log handler
    LOGGER_HANDLER_POLICY = 'never'
    HOST = '0.0.0.0'
    TESTING = False
    SHOW_DB_URI = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'replace-me-with-something-random'
    JWT_ERROR_MESSAGE_KEY = 'message'
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access']
    JWT_IDENTITY_CLAIM = 'sub'
    # Default the access tokens to expire after one hour
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    CORS_URL = '*'
    AD_USE_NTLM = True
    MINIMUM_QUESTIONS = 3


class ProdConfig(Config):
    """The production ADReset application configuration."""

    DEBUG = False


class DevConfig(Config):
    """The development ADReset application configuration."""

    SQLALCHEMY_DATABASE_URI = 'sqlite:///{0}'.format(os.path.join(base_dir, 'adreset.db'))
    JSONIFY_PRETTYPRINT_REGULAR = True


class TestConfig(Config):
    """The test ADReset application configuration."""

    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True
    # ldap3 mocking doesn't support NTLM
    AD_USE_NTLM = False
    AD_DOMAIN = 'adreset.local'
    AD_LDAP_URI = 'ldaps://server.domain.local:636'
    AD_USERS_GROUP = 'ADReset Users'
    AD_ADMINS_GROUP = 'ADReset Admins'
    AD_SERVICE_USERNAME = 'CN=testuser,OU=ADReset,DC=adreset,DC=local'
    AD_SERVICE_PASSWORD = 'P@ssw0rd'
