# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from sqlalchemy.orm import validates
from six import string_types
from flask import url_for
import passlib.hash

from adreset.models import db
from adreset.error import ValidationError


_must_be_str = 'The {0} must be a string'


class Question(db.Model):
    """Contain the secret questions the administrator decides to configure ADReset with."""

    id = db.Column(db.Integer(), primary_key=True)
    question = db.Column(db.String(256), nullable=False, unique=True)
    answers = db.relationship('Answer', backref='question')
    enabled = db.Column(db.Boolean, default=True, nullable=False)

    @validates('question')
    def validate_question(self, key, question):
        """
        Ensure the question is a string of 256 characters or less.

        :param str key: the key/column being validated
        :param str question: the question being validated
        :return: the question being validated
        :rtype: str
        :raises ValidationError: if the string is more than 256 characters
        :raises RuntimeError: if the question is an invalid type
        """
        if not isinstance(question, string_types):
            raise RuntimeError(_must_be_str.format(key))
        elif len(question) > 256:
            raise ValidationError('The question must be less than 256 characters')
        return question

    def to_json(self, include_url=True):
        """Represent the row as a dictionary for JSON output."""
        rv = {
            'id': self.id,
            'question': self.question,
            'enabled': self.enabled,
        }
        if include_url:
            rv['url'] = url_for('api_v1.get_question', question_id=self.id, _external=True)
        return rv


class Answer(db.Model):
    """Contain the user's answers to the secret questions they've chosen."""

    id = db.Column(db.Integer(), primary_key=True)
    # The hashed answer should be around 120 characters, but give it plenty of room to expand in
    # the event the hashing algorithm is updated
    answer = db.Column(db.String(256), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    question_id = db.Column(
        db.Integer(), db.ForeignKey('question.id', ondelete='CASCADE'), nullable=False
    )

    @validates('answer')
    def validate_answer(self, key, answer):
        """
        Ensure the answer is hashed.

        :param str key: the key/column being validated
        :param str answer: the answer being validated
        :return: the answer being validated
        :rtype: str
        :raises RuntimeError: if the answer is not hashed or isn't a string
        """
        if not isinstance(answer, string_types):
            raise RuntimeError(_must_be_str.format(key))
        elif not passlib.hash.sha512_crypt.identify(answer):
            raise RuntimeError('The answer must be stored as a SHA512 hash')
        return answer

    @staticmethod
    def hash_answer(answer):
        """
        Hash the answer using the SHA512 algorithm.

        :param str answer: the answer to hash
        :return: a SHA512 hash of the string
        :rtype: str
        """
        return passlib.hash.sha512_crypt.hash(answer)

    @staticmethod
    def verify_answer(input_answer, hashed_answer):
        """
        Verify the input answer and the hashed answer stored in the database are the same.

        :param str input_answer: the answer to verify
        :param str hashed_answer: the hashed answer to verify against
        :return: a boolean determining if the answers match
        :rtype: bool
        """
        return passlib.hash.sha512_crypt.verify(input_answer, hashed_answer)

    def to_json(self, include_url=True):
        """Represent the row as a dictionary for JSON output."""
        rv = {
            'id': self.id,
            'user_id': self.user_id,
            'question': self.question.to_json(),
        }
        if include_url:
            rv['url'] = url_for('api_v1.get_answer', answer_id=self.id, _external=True)
        return rv
