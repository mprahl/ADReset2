# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

import pytest

from adreset.app import create_app


@pytest.fixture(scope='session')
def client():
    """Pytest fixture that creates a Flask application object for the pytest session."""
    return create_app('adreset.config.TestConfig').test_client()
