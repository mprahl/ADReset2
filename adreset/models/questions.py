# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from sqlalchemy.orm import validates
from six import string_types
from flask import url_for

from adreset.models import db
from adreset.error import ValidationError


_must_be_str = 'The {0} must be a string'
_256_or_less = 'The {0} must be less than 256 characters'


class Question(db.Model):
    """Contain the secret questions the administrator decides to configure ADReset with."""

    id = db.Column(db.Integer(), primary_key=True)
    question = db.Column(db.String(256), nullable=False, unique=True)
    answers = db.relationship('Answer', backref='question')

    @validates('question')
    def validate_question(self, key, question):
        """
        Ensure the question is a string of 256 characters or less.

        :param str key: the key/column being validated
        :param str question: the question being validated
        :return: the question being validated
        :rtype: str
        :raises ValidationError: if the string is more than 256 characters or it is an invalid type
        """
        if not isinstance(question, string_types):
            raise ValidationError(_must_be_str.format(key))
        elif len(question) > 256:
            raise ValidationError(_256_or_less.format(key))
        return question

    def to_json(self, include_url=True):
        """Represent the row as a dictionary for JSON output."""
        rv = {
            'id': self.id,
            'question': self.question
        }
        if include_url:
            rv['url'] = url_for('api_v1.get_question', question_id=self.id, _external=True)
        return rv


class Answer(db.Model):
    """Contain the user's answers to the secret questions they've chosen."""

    id = db.Column(db.Integer(), primary_key=True)
    answer = db.Column(db.String(256), nullable=False)
    user_id = db.Column(
        db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    question_id = db.Column(
        db.Integer(), db.ForeignKey('question.id', ondelete='CASCADE'), nullable=False)
