# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from flask import Blueprint, jsonify, request
from six import string_types
from flask_jwt_extended import create_access_token, jwt_required, get_raw_jwt

from adreset import version
from adreset.error import ValidationError
from adreset.ad import AD
from adreset.models import db, User, BlacklistedToken


api_v1 = Blueprint('api_v1', __name__)


@api_v1.route('/about')
def about():
    """
    Display general information about the app.

    :rtype: flask.Response
    """
    return jsonify({'version': version})


@api_v1.route('/login', methods=['POST'])
def login():
    """
    Login the user using their Active Directory credentials.

    :rtype: flask.Response
    """
    req_json = request.get_json(force=True)
    for required in ('username', 'password'):
        if required not in req_json:
            raise ValidationError('The "{0}" parameter was not provided'.format(required))
        if not isinstance(req_json[required], string_types):
            raise ValidationError('The "{0}" parameter must be a string'.format(required))

    ad = AD()
    ad.login(req_json['username'], req_json['password'])
    guid = ad.get_guid(ad.get_loggedin_user())
    user = User.query.filter_by(ad_guid=guid).first()
    # If the user doesn't exist in the database, this must be their first time logging in,
    # therefore, an entry for that user must be added to the database
    if not user:
        ad.log('debug', 'The user doesn\'t exist in the database, so it will be created')
        user = User(ad_guid=guid)
        db.session.add(user)
        db.session.commit()
        ad.log('debug', 'The user was successfully created in the database')
    # The token's identity uses the user's GUID since that is unique across the AD Forest and won't
    # change if the account gets renamed
    token = create_access_token(identity=user.ad_guid)
    return jsonify({'token': token})


@api_v1.route('/logout', methods=['POST'])
@jwt_required
def logout():
    """
    Logout the user by revoking their token.

    :rtype: flask.Response
    """
    jwt = get_raw_jwt()
    # Store the token in the database status of not currently revoked
    BlacklistedToken.add_token(jwt)
    return jsonify({'message': 'You were logged out successfully'})
