# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from flask import Blueprint, jsonify

from adreset import version


api_v1 = Blueprint('api_v1', __name__)


@api_v1.route('/about')
def about():
    """
    Display general information about the app.

    :rtype: flask.Response
    """
    return jsonify({'version': version})
