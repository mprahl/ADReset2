# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from os import path

import ldap3
from mock import patch, PropertyMock
import pytest

from adreset.app import create_app
from adreset.models import db
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
        mock_server, client_strategy=ldap3.MOCK_SYNC, authentication=ldap3.SIMPLE)
    ldap_entries_path = path.join(path.abspath(path.dirname(__file__)), 'ad', 'directory.json')
    mock_connection.strategy.entries_from_json(ldap_entries_path)

    # Patch the connection property method to return the mock connection instead
    with patch('adreset.ad.AD.connection', new_callable=PropertyMock) as mock_ad_connection:
        mock_ad_connection.return_value = mock_connection
        yield adreset.ad.AD()

    mock_connection.unbind()
