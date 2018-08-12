# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

import os
from datetime import datetime

from flask import Flask, current_app
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from werkzeug.exceptions import default_exceptions

from adreset.logger import init_logging
from adreset.error import json_error, ValidationError, ConfigurationError, ADError
from adreset.api.v1 import api_v1
from adreset.models import db, BlacklistedToken


def load_config(app):
    """
    Determine the correct configuration to use and apply it.

    :param flask.Flask app: a Flask application object
    """
    if app.config['ENV'] == 'development':
        default_config_obj = 'adreset.config.DevConfig'
    else:
        default_config_obj = 'adreset.config.ProdConfig'

    app.config.from_object(default_config_obj)
    config_file = os.environ.get('ADRESET_CONFIG')
    if config_file and os.path.isfile(config_file):
        app.config.from_pyfile(config_file)

    if os.environ.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
    if os.environ.get('DB_URI'):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']


def insert_headers(response):
    """
    Insert configured HTTP headers into the Flask response.

    :param flask.Response response: the response to insert headers into
    :return: modified Flask response
    :rtype: flask.Response
    """
    cors_url = current_app.config.get('CORS_URL')
    if cors_url:
        response.headers['Access-Control-Allow-Origin'] = cors_url
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response


def create_db():
    """Run db.create_all()."""
    db.create_all()


def create_app(config_obj=None):
    """
    Create a Flask application object.

    :return: a Flask application object
    :rtype: flask.Flask
    """
    app = Flask(__name__)
    if config_obj:
        app.config.from_object(config_obj)
    else:
        load_config(app)

    if app.config['ENV'] != 'development':
        if app.config['SECRET_KEY'] == 'replace-me-with-something-random':
            raise RuntimeError('You need to change the SECRET_KEY configuration for production')
    for config in ('AD_DOMAIN', 'AD_LDAP_URI', 'SQLALCHEMY_DATABASE_URI'):
        if not app.config.get(config):
            raise RuntimeError('You need to set the "{0}" setting'.format(config))

    init_logging(app)
    db.init_app(app)
    migrations_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'migrations')
    Migrate(app, db, directory=migrations_dir)
    app.cli.command()(create_db)

    for status_code in default_exceptions.keys():
        app.register_error_handler(status_code, json_error)
    app.register_error_handler(ValidationError, json_error)
    app.register_error_handler(ConfigurationError, json_error)
    app.register_error_handler(ADError, json_error)

    app.after_request(insert_headers)
    app.register_blueprint(api_v1, url_prefix='/api/v1')

    jwt = JWTManager(app)
    jwt.token_in_blacklist_loader(BlacklistedToken.is_token_revoked)
    app.cli.command()(prune_blacklisted_tokens)

    return app


def prune_blacklisted_tokens():
    """Delete blacklisted tokens that have expired from the database."""
    expired = BlacklistedToken.query.filter(BlacklistedToken.expires < datetime.now()).all()
    if expired:
        print('Removing {0} expired blacklisted tokens'.format(len(expired)))
        for token in expired:
            db.session.delete(token)
        db.session.commit()
    else:
        print('No expired blacklisted tokens to remove')
