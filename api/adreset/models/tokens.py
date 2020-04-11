# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from datetime import datetime

from adreset.models import db, User


class BlacklistedToken(db.Model):
    """Contain issued JSON web tokens."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    jti = db.Column(db.String(36), nullable=False)
    expires = db.Column(db.DateTime, nullable=False)

    @staticmethod
    def add_token(token):
        """
        Add a new token to the database in the unrevoked state.

        :param dict token: the decoded token to blacklist
        """
        user = User.query.filter_by(ad_guid=token['sub']['guid']).one()
        db_token = BlacklistedToken(
            jti=token['jti'], user_id=user.id, expires=datetime.fromtimestamp(token['exp'])
        )
        db.session.add(db_token)
        db.session.commit()

    @staticmethod
    def is_token_revoked(token):
        """
        Check if the token is revoked and default to True if the token is not present.

        :param dict token: the decoded JSON web token to check
        :rtype: bool
        :return: a boolean representing if the token is revoked
        """
        jti = token['jti']
        return bool(BlacklistedToken.query.filter_by(jti=jti).first())

    @staticmethod
    def revoke_token(jti):
        """
        Revoke a token for the given user.

        :param str jti: the GUID that identifies the token
        :raises werkzeug.exceptions.NotFound: if the specified token does not exist in the database
        """
        return bool(BlacklistedToken.query.filter_by(jti=jti).first())
