# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

import json

from adreset import version


def test_about(client):
    """Test the /api/v1/about route."""
    rv = client.get('/api/v1/about')
    assert json.loads(rv.data.decode('utf-8')) == {'version': version}


def test_insert_headers(client):
    """Test that the appropriate headers are inserted in a Flask response."""
    rv = client.get('/api/v1/')
    assert 'Access-Control-Allow-Origin: *' in str(rv.headers)
    assert 'Access-Control-Allow-Headers: Content-Type' in str(rv.headers)
    assert 'Access-Control-Allow-Method: GET, OPTIONS' in str(rv.headers)
