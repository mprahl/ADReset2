# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from adreset.models import db


class Question(db.Model):
    """Contain the secret questions the administrator decides to configure ADReset with."""

    id = db.Column(db.Integer(), primary_key=True)
    question = db.Column(db.String(256), nullable=False, unique=True)
    answers = db.relationship('Answer', backref='question')


class Answer(db.Model):
    """Contain the user's answers to the secret questions they've chosen."""

    id = db.Column(db.Integer(), primary_key=True)
    answer = db.Column(db.String(256), nullable=False)
    user_id = db.Column(
        db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    question_id = db.Column(
        db.Integer(), db.ForeignKey('question.id', ondelete='CASCADE'), nullable=False)
