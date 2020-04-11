# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

# Add some imports so that you can do `from adreset.models import Question`. It also makes
# SQLAlchemy aware of the models whenever `db` is imported.
from adreset.models.questions import Answer, Question  # noqa: F401
from adreset.models.users import FailedAttempt, User  # noqa: F401
from adreset.models.tokens import BlacklistedToken  # noqa: F401
