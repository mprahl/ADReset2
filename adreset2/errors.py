"""
Author: StackFocus
File: errors.py
Purpose: defines error handling functions
"""
from flask import jsonify


class ValidationError(ValueError):
    """ A custom exception used for invalid input or values
    """
    pass


class GenericError(Exception):
    """ A custom exception used for an unknown error
    """
    pass


class ADException(Exception):
    """ A custom exception for the PostMasterLDAP class
    """
    pass


def bad_request(message):
    response = jsonify(
        {'status': 400,
         'error': 'bad request',
         'message': message})
    response.status_code = 400
    return response


def not_found(message):
    response = jsonify(
        {'status': 404,
         'error': 'not found',
         'message': message})
    response.status_code = 404
    return response
