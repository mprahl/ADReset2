# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from flask import jsonify
from werkzeug.exceptions import HTTPException


class ValidationError(ValueError):
    """A custom exception handled by Flask to denote bad user input."""

    pass


class ConfigurationError(ValueError):
    """A custom exception handled by Flask to denote a bad configuration."""

    pass


class ADError(ValueError):
    """A custom exception handled by Flask to denote an error with Active Directory."""

    pass


def json_error(error):
    """
    Convert exceptions to JSON responses.

    :param Exception error: an Exception to convert to JSON
    :return: a Flask JSON response
    :rtype: flask.Response
    """
    if isinstance(error, HTTPException):
        response = jsonify({
            'status': error.code,
            'message': error.description
        })
        response.status_code = error.code
    else:
        status_code = 500
        message = None
        if isinstance(error, ValidationError):
            status_code = 400

        response = jsonify({
            'status': status_code,
            'message': message or str(error)
        })
        response.status_code = status_code
    return response
