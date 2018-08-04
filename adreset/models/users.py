# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from adreset.models import db


class User(db.Model):
    """Represent the Active Directory user."""

    id = db.Column(db.Integer(), primary_key=True)
    # We store the GUID as a string for easier auditing in Active Directory. This must be 36
    # characters because the GUID as a string is 32 characters + 4 hyphens.
    ad_guid = db.Column(db.String(36), nullable=False, unique=True, index=True)
    answers = db.relationship('adreset.models.questions.Answer', backref='user')
    blacklisted_tokens = db.relationship('adreset.models.tokens.BlacklistedToken', backref='user')
