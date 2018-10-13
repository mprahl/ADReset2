# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from functools import wraps

from werkzeug.exceptions import Forbidden
from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims


def admin_required(func):
    """Verify the token and ensure the user is an admin."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if 'admin' not in claims['roles']:
            raise Forbidden('You must be an administrator to proceed with this action')
        else:
            return func(*args, **kwargs)
    return wrapper


def user_required(func):
    """Verify the token and ensure the user is not an admin."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if 'user' not in claims['roles']:
            raise Forbidden('Administrators are not authorized to proceed with this action')
        else:
            return func(*args, **kwargs)
    return wrapper
