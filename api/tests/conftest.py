# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from os import path

import ldap3
from mock import patch, PropertyMock
import pytest
from flask_jwt_extended import create_access_token

from adreset.app import create_app
from adreset.models import db, User, Question
import adreset.ad


@pytest.fixture(scope='session')
def app():
    """Pytest fixture that creates a Flask app object with an established context."""
    app = create_app('adreset.config.TestConfig')
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.fixture(autouse=True)
def setup_db(app):
    """Reinitialize the database before each test."""
    db.session.remove()
    db.drop_all()
    db.create_all()
    question = Question(question='What is your favorite flavor of ice cream?')
    question2 = Question(question='What is your favorite color?')
    question3 = Question(question='What is your favorite toy?')
    db.session.add(question)
    db.session.add(question2)
    db.session.add(question3)
    db.session.commit()


@pytest.fixture(scope='session')
def client(app):
    """Pytest fixture that creates a Flask test client object for the pytest session."""
    with app.test_client() as client:
        yield client


@pytest.fixture(scope='function')
# Request the app fixture to establish a context so the AD class can get config options from Flask
def mock_ad(app):
    """Pytest fixture that mocks an LDAP directory."""
    # Create a mock LDAP directory
    mock_server = ldap3.Server(app.config['AD_LDAP_URI'], get_info=ldap3.OFFLINE_AD_2012_R2)
    mock_connection = ldap3.Connection(
        mock_server, client_strategy=ldap3.MOCK_SYNC, authentication=ldap3.SIMPLE
    )
    ldap_entries_path = path.join(path.abspath(path.dirname(__file__)), 'ad', 'directory.json')
    mock_connection.strategy.entries_from_json(ldap_entries_path)

    # Patch the connection property method to return the mock connection instead
    with patch('adreset.ad.AD.connection', new_callable=PropertyMock) as mock_ad_connection:
        mock_ad_connection.return_value = mock_connection
        yield adreset.ad.AD()

    mock_connection.unbind()


# ldap3 testing doesn't support the AD specific searches such as nested group memberships,
# so we must mock those ahead of time.
@pytest.fixture(scope='function')
def mock_admin_ad(mock_ad):
    """Pytest fixture that mocks an LDAP directory for user logins."""
    with patch.object(mock_ad, 'check_user_group_membership', return_value=False):
        with patch.object(mock_ad, 'check_admin_group_membership', return_value=True):
            with patch('adreset.ad.AD', return_value=mock_ad):
                yield mock_ad


@pytest.fixture(scope='function')
def mock_user_ad(mock_ad):
    """Pytest fixture that mocks an LDAP directory for user logins."""
    with patch.object(mock_ad, 'check_user_group_membership', return_value=True):
        with patch.object(mock_ad, 'check_admin_group_membership', return_value=False):
            with patch('adreset.ad.AD', return_value=mock_ad):
                yield mock_ad


@pytest.fixture(scope='function')
def admin_logged_in_headers(mock_admin_ad):
    """Pytest fixture that creates a valid token for an admin."""
    # This is the GUID for "testuser" which is a member of "ADReset Admins"
    guid = '5609c5ec-c0df-4480-a94b-b6eb0fc4c066'
    user = User(ad_guid=guid)
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity={'guid': guid, 'username': 'testuser'})
    return {'Authorization': 'Bearer {0}'.format(token), 'Content-Type': 'application/json'}


@pytest.fixture(scope='function')
def logged_in_headers(mock_user_ad):
    """Pytest fixture that creates a valid token for a user."""
    # This is the GUID for "testuser2" which is a member of "ADReset Users"
    guid = '10385a23-6def-4990-84a8-32444e36e496'
    user = User(ad_guid=guid)
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity={'guid': guid, 'username': 'testuser2'})
    return {'Authorization': 'Bearer {0}'.format(token), 'Content-Type': 'application/json'}
