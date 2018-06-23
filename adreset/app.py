# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

import os

from flask import Flask, current_app
from werkzeug.exceptions import default_exceptions

from adreset.logger import init_logging
from adreset.error import json_error, ValidationError
from adreset.api.v1 import api_v1


def load_config(app):
    """
    Determine the correct configuration to use and apply it.

    :param flask.Flask app: a Flask application object
    """
    if os.getenv('DEV') and os.getenv('DEV').lower() == 'true':
        default_config_obj = 'adreset.config.DevConfig'
    else:
        default_config_obj = 'adreset.config.ProdConfig'

    app.config.from_object(default_config_obj)
    config_file = os.environ.get('ADRESET_CONFIG')
    if config_file and os.path.isfile(config_file):
        app.config.from_pyfile(config_file)

    if os.environ.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ['SECRET_KEY']


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
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Method'] = 'GET, OPTIONS'
    return response


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

    if app.config['PRODUCTION'] and app.secret_key == 'replace-me-with-something-random':
        raise Warning('You need to change the app.secret_key value for production')

    init_logging(app)

    for status_code in default_exceptions.keys():
        app.register_error_handler(status_code, json_error)
    app.register_error_handler(ValidationError, json_error)
    app.register_blueprint(api_v1, url_prefix='/api/v1')

    app.after_request(insert_headers)

    return app
