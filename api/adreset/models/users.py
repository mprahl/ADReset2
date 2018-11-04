# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy import func

from adreset.models import db


class User(db.Model):
    """Represent the Active Directory user."""

    id = db.Column(db.Integer(), primary_key=True)
    # We store the GUID as a string for easier auditing in Active Directory. This must be 36
    # characters because the GUID as a string is 32 characters + 4 hyphens.
    ad_guid = db.Column(db.String(36), nullable=False, unique=True, index=True)
    answers = db.relationship('adreset.models.questions.Answer', backref='user')
    blacklisted_tokens = db.relationship('adreset.models.tokens.BlacklistedToken', backref='user')
    failed_reset__attempts = db.relationship('FailedAttempt', backref='user')

    @staticmethod
    def is_user_locked_out(user_id):
        """
        Check if the passed-in user is locked out.

        :param int user_id: the user ID to check
        :return: a boolean determining if the user is locked out
        :rtype: bool
        """
        lockout_mins = current_app.config['LOCKOUT_MINUTES']
        lockout_datetime = datetime.utcnow() - timedelta(minutes=lockout_mins)
        failed_attempts = (db.session.query(func.count(FailedAttempt.id))).filter(
            FailedAttempt.time >= lockout_datetime).scalar()
        return failed_attempts >= current_app.config['ATTEMPTS_BEFORE_LOCKOUT']

    def is_locked_out(self):
        """
        Check if the current user is locked out.

        :return: a boolean determining if the user is locked out
        :rtype: bool
        """
        return self.is_user_locked_out(self.id)


class FailedAttempt(db.Model):
    """Represent a failed password reset attempt."""

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    time = db.Column(db.DateTime, nullable=False)
