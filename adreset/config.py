# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals


class Config(object):
    """The base ADReset application configuration."""

    DEBUG = True
    # We configure logging explicitly, turn off the Flask-supplied log handler
    LOGGER_HANDLER_POLICY = 'never'
    HOST = '0.0.0.0'
    PRODUCTION = False
    SHOW_DB_URI = False
    SECRET_KEY = 'replace-me-with-something-random'
    CORS_URL = '*'


class ProdConfig(Config):
    """The production ADReset application configuration."""

    DEBUG = False
    PRODUCTION = True


class DevConfig(Config):
    """The development ADReset application configuration."""

    JSONIFY_PRETTYPRINT_REGULAR = True


class TestConfig(Config):
    """The test ADReset application configuration."""

    pass
