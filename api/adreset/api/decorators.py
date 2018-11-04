# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from functools import wraps

from flask import jsonify, request, url_for
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


def paginate(func):
    """Paginate the SQLAlchemy query and return a JSON Flask response."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        page = request.args.get('page', 1, type=int)
        # Make sure the per_page argument is below the maximum of 100
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        # Get the SQLAlchemy query that was returned from the route
        query = func(*args, **kwargs)
        # Paginate the returned query
        p = query.paginate(page, per_page)

        # Generate the pagination metadata
        pages = {
            'next': None,
            'page': page,
            'pages': p.pages,
            'previous': None,
            'per_page': per_page,
            'total': p.total,
        }
        if p.has_prev:
            pages['previous'] = url_for(
                request.endpoint, page=p.prev_num, per_page=per_page, _external=True, **kwargs)

        if p.has_next:
            pages['next'] = url_for(
                request.endpoint, page=p.next_num, per_page=per_page, _external=True, **kwargs)

        pages['first'] = url_for(
            request.endpoint, page=1, per_page=per_page, _external=True, **kwargs)
        pages['last'] = url_for(
            request.endpoint, page=p.pages, per_page=per_page, _external=True, **kwargs)

        return jsonify({
            'items': [item.to_json() for item in p.items],
            'meta': pages
        })

    return wrapper
