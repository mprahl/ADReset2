# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

import json

import flask_jwt_extended

from adreset import version
from adreset.models import User


def test_about(client):
    """Test the /api/v1/about route."""
    rv = client.get('/api/v1/about')
    assert json.loads(rv.data.decode('utf-8')) == {'version': version}


def test_insert_headers(client):
    """Test that the appropriate headers are inserted in a Flask response."""
    rv = client.get('/api/v1/')
    assert 'Access-Control-Allow-Origin: *' in str(rv.headers)
    assert 'Access-Control-Allow-Headers: Content-Type' in str(rv.headers)
    assert 'Access-Control-Allow-Methods: GET, POST, OPTIONS' in str(rv.headers)


def test_login(client, mock_user_ad):
    """Test that logins are successfull."""
    # Make sure the user doesn't exist before the first login
    assert len(User.query.all()) == 0
    # Because we are mocking AD with ldap3, we have to use the distinguished name to log in
    rv = client.post('/api/v1/login', data=json.dumps({
        'username': 'CN=testuser2,OU=ADReset,DC=adreset,DC=local',
        'password': 'P@ssW0rd'}))
    assert rv.status_code == 200
    rv_json = json.loads(rv.data.decode('utf-8'))
    assert set(rv_json.keys()) == set(['token'])
    # Make sure the user was created after the first login
    guid = '10385a23-6def-4990-84a8-32444e36e496'
    assert User.query.filter_by(ad_guid=guid).first()
    decoded_token = flask_jwt_extended.decode_token(rv_json['token'])
    assert decoded_token['sub'] == guid
    assert decoded_token['user_claims']['roles'] == ['user']


def test_admin_login(client, mock_admin_ad):
    """Test that admin logins are successfull."""
    # Make sure the user doesn't exist before the first login
    assert len(User.query.all()) == 0
    # Because we are mocking AD with ldap3, we have to use the distinguished name to log in
    rv = client.post('/api/v1/login', data=json.dumps({
        'username': 'CN=testuser,OU=ADReset,DC=adreset,DC=local',
        'password': 'P@ssW0rd'}))
    assert rv.status_code == 200
    rv_json = json.loads(rv.data.decode('utf-8'))
    assert set(rv_json.keys()) == set(['token'])
    # Make sure the user was created after the first login
    guid = '5609c5ec-c0df-4480-a94b-b6eb0fc4c066'
    assert User.query.filter_by(ad_guid=guid).first()
    decoded_token = flask_jwt_extended.decode_token(rv_json['token'])
    assert decoded_token['sub'] == guid
    assert decoded_token['user_claims']['roles'] == ['admin']


def test_logout(client, logged_in_headers):
    """Test that logouts are successfull."""
    rv = client.post('/api/v1/logout', headers=logged_in_headers)
    assert rv.status_code == 200
    rv_json = json.loads(rv.data.decode('utf-8'))
    assert rv_json['message'] == 'You were logged out successfully'

    # Make sure that if the user tries to log out with the same token they get an error
    # saying their token is revoked
    rv = client.post('/api/v1/logout', headers=logged_in_headers)
    assert rv.status_code == 401
    rv_json = json.loads(rv.data.decode('utf-8'))
    assert rv_json['message'] == 'Token has been revoked'


def test_user_protected(client, logged_in_headers, admin_logged_in_headers):
    """Test the /api/v1/protected route."""
    rv = client.get('/api/v1/protected', headers=logged_in_headers)
    assert json.loads(rv.data.decode('utf-8')) == {'message': 'placeholder'}

    rv = client.get('/api/v1/protected', headers=admin_logged_in_headers)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'Administrators are not authorized to proceed with this action',
        'status': 403
    }


def test_admin_protected(client, logged_in_headers, admin_logged_in_headers):
    """Test the /api/v1/protected route."""
    rv = client.get('/api/v1/admin-protected', headers=logged_in_headers)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'You must be an administrator to proceed with this action',
        'status': 403
    }

    rv = client.get('/api/v1/admin-protected', headers=admin_logged_in_headers)
    assert json.loads(rv.data.decode('utf-8')) == {'message': 'placeholder'}
