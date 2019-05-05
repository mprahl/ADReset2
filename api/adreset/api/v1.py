# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

from datetime import datetime
import copy

from flask import Blueprint, jsonify, request, current_app
from werkzeug.exceptions import NotFound, Unauthorized
from six import string_types
from flask_jwt_extended import create_access_token, jwt_required, get_raw_jwt, get_jwt_identity
from sqlalchemy import func

from adreset import version, log
from adreset.error import ValidationError
import adreset.ad
from adreset.models import db, User, BlacklistedToken, Question, Answer, FailedAttempt
from adreset.api.decorators import paginate, admin_required, user_required


api_v1 = Blueprint('api_v1', __name__)


def _validate_api_input(json_req, key, expected_type):
    """
    Validate the API input to ensure it is not empty and the correct type.

    :param dict json_req: the JSON of the Flask request
    :param str key: the key of the input to validate
    :param type expected_type: the type the input should be
    :raises ValidationError: if the input is empty or the wrong type
    """
    value = json_req.get(key)
    if value is not False and value != 0 and not value:
        raise ValidationError('The parameter "{0}" must not be empty'.format(key))
    elif not isinstance(value, expected_type):
        if expected_type == str or expected_type == string_types:
            type_name = 'string'
        elif expected_type == dict:
            type_name = 'object'
        elif expected_type == list:
            type_name = 'array'
        elif expected_type == int:
            type_name = 'integer'
        elif expected_type == bool:
            type_name = 'boolean'
        else:
            type_name = expected_type.__name__

        raise ValidationError('The parameter "{0}" must be a {1}'.format(key, type_name))


def _str_to_bool(candidate):
    """
    Parse the string to convert it to a boolean if possible.

    :param str candidate: the string to parse
    :return: a parsed boolean or None if it can't be parsed
    :rtype: bool/None
    """
    if not candidate:
        return None

    if candidate.lower() in ('1', 'true'):
        return True
    elif candidate.lower() in ('0', 'false'):
        return False
    else:
        return None


@api_v1.route('/about')
def about():
    """
    Display general information about the app.

    :rtype: flask.Response
    """
    return jsonify({
        'allow_duplicate_answers': current_app.config['ALLOW_DUPLICATE_ANSWERS'],
        'answers_minimum_length': current_app.config['ANSWERS_MINIMUM_LENGTH'],
        'required_answers': current_app.config['REQUIRED_ANSWERS'],
        'version': version
    })


@api_v1.route('/login', methods=['POST'])
def login():
    """
    Login the user using their Active Directory credentials.

    :rtype: flask.Response
    """
    req_json = request.get_json(force=True)
    _validate_api_input(req_json, 'username', string_types)
    _validate_api_input(req_json, 'password', string_types)

    ad = adreset.ad.AD()
    ad.login(req_json['username'], req_json['password'])
    username = ad.get_loggedin_user()
    guid = ad.get_guid(username)
    user = User.query.filter_by(ad_guid=guid).first()
    # If the user doesn't exist in the database, this must be their first time logging in,
    # therefore, an entry for that user must be added to the database
    if not user:
        ad.log('debug', 'The user doesn\'t exist in the database, so it will be created')
        user = User(ad_guid=guid)
        db.session.add(user)
        db.session.commit()
        ad.log('debug', 'The user was successfully created in the database')
    # The token's identity has the user's GUID since that is unique across the AD Forest and won't
    # change if the account gets renamed
    token = create_access_token(identity={'guid': user.ad_guid, 'username': username})
    return jsonify({'token': token})


@api_v1.route('/logout', methods=['POST'])
@jwt_required
def logout():
    """
    Logout the user by revoking their token.

    :rtype: flask.Response
    """
    jwt = get_raw_jwt()
    # Store the token in the database status of not currently revoked
    BlacklistedToken.add_token(jwt)
    return jsonify({'message': 'You were logged out successfully'})


@api_v1.route('/questions')
@paginate
def get_questions():
    """
    List all the questions.

    :rtype: flask.Response
    """
    query = Question.query
    enabled = _str_to_bool(request.args.get('enabled'))
    if enabled is not None:
        query = query.filter_by(enabled=enabled)
    return query


@api_v1.route('/questions/<int:question_id>')
def get_question(question_id):
    """
    List a specific question.

    :rtype: flask.Response
    """
    question = Question.query.get(question_id)
    if question:
        return jsonify(question.to_json(include_url=False))
    else:
        raise NotFound('The question was not found')


@api_v1.route('/questions', methods=['POST'])
@admin_required
def add_question():
    """
    Add a question that users can use for their secret answers.

    :rtype: flask.Response
    """
    req_json = request.get_json(force=True)
    _validate_api_input(req_json, 'question', string_types)
    if 'enabled' in req_json:
        _validate_api_input(req_json, 'enabled', bool)

    exists = bool((db.session.query(func.count(Question.question))).filter_by(
        question=req_json['question']).scalar())
    if exists:
        raise ValidationError('The supplied question already exists')

    question = Question(question=req_json['question'])
    if 'enabled' in req_json:
        question.enabled = req_json['enabled']
    db.session.add(question)
    db.session.commit()
    return jsonify(question.to_json()), 201


@api_v1.route('/questions/<int:question_id>', methods=['PATCH'])
@admin_required
def patch_question(question_id):
    """
    Patch a question that users can use for their secret answers.

    :rtype: flask.Response
    """
    req_json = request.get_json(force=True)
    valid_keys = set(['question', 'enabled'])
    if not valid_keys.issuperset(set(req_json.keys())):
        raise ValidationError('Invalid keys were supplied. Please use the following keys: {0}'
                              .format(', '.join(sorted(valid_keys))))

    question = Question.query.get(question_id)
    if not question:
        raise NotFound('The question was not found')

    if 'question' in req_json:
        _validate_api_input(req_json, 'question', string_types)
        question.question = req_json['question']

    if 'enabled' in req_json:
        _validate_api_input(req_json, 'enabled', bool)
        question.enabled = req_json['enabled']

    db.session.commit()
    return jsonify(question.to_json()), 200


@api_v1.route('/answers')
@user_required
@paginate
def get_answers():
    """
    List all the answers associated with the user.

    :rtype: flask.Response
    """
    user_ad_guid = get_jwt_identity()['guid']
    user_id = db.session.query(User.id).filter_by(ad_guid=user_ad_guid).scalar()
    return Answer.query.filter_by(user_id=user_id)


@api_v1.route('/answers/<username>')
@paginate
def get_answers_unauthenticated(username):
    """
    List all the answers associated with the input user.

    :rtype: flask.Response
    """
    user_id = User.get_id_from_ad_username(username)
    return Answer.query.filter_by(user_id=user_id)


@api_v1.route('/answers/<int:answer_id>')
@user_required
def get_answer(answer_id):
    """
    List a specific answer.

    :rtype: flask.Response
    """
    user_ad_guid = get_jwt_identity()['guid']
    user_id = db.session.query(User.id).filter_by(ad_guid=user_ad_guid).scalar()
    answer = Answer.query.get(answer_id)
    if answer:
        if answer.user_id == user_id:
            return jsonify(answer.to_json(include_url=False))
        else:
            raise Unauthorized('This answer is not associated with your account')
    else:
        raise NotFound('The answer was not found')


@api_v1.route('/answers', methods=['DELETE'])
@user_required
def delete_answers():
    """
    Delete the user's configured answers.

    :rtype: flask.Response
    """
    user_ad_guid = get_jwt_identity()['guid']
    user_id = db.session.query(User.id).filter_by(ad_guid=user_ad_guid).scalar()
    answers = Answer.query.filter_by(user_id=user_id).all()
    for answer in answers:
        db.session.delete(answer)
    db.session.commit()
    return jsonify({}), 204


@api_v1.route('/answers', methods=['POST'])
@user_required
def add_answers():
    """
    Add a user's secret answers tied to administrator approved questions.

    :rtype: flask.Response
    """
    user_ad_guid = get_jwt_identity()['guid']
    user_id = db.session.query(User.id).filter_by(ad_guid=user_ad_guid).scalar()
    username = get_jwt_identity()['username']
    # Make sure the user hasn't already set the required amount of secret answers
    num_answers_in_db = \
        (db.session.query(func.count(Answer.answer))).filter_by(user_id=user_id).scalar()
    if num_answers_in_db != 0:
        log.debug({
            'message': 'The user attempted to set their secret answers but had them already set',
            'user': username,
        })
        raise ValidationError(
            'You\'ve previously set your secret answers. Please reset them to set them again.')

    req_json = copy.deepcopy(request.get_json(force=True))
    if not isinstance(req_json, list):
        log.debug({'message': 'The user did not supply an array', 'user': username})
        raise ValidationError('The input must be an array')

    num_answers = len(req_json)
    # Verify that the user supplied the required amount of answers
    if num_answers != current_app.config['REQUIRED_ANSWERS']:
        log.info({'message': 'The user supplied an invalid amount of answers', 'user': username})
        if num_answers == 1:
            error_prefix = '1 answer was'
        else:
            error_prefix = '{0} answers were'.format(num_answers)
        raise ValidationError('{0} supplied but {1} are required'.format(
            error_prefix,
            current_app.config['REQUIRED_ANSWERS']
        ))

    question_ids = set()
    answer_strings = set()
    for answer in req_json:
        _validate_api_input(answer, 'answer', string_types)
        _validate_api_input(answer, 'question_id', int)
        # Verify the answers meet the length requirements
        if len(answer['answer']) < current_app.config['ANSWERS_MINIMUM_LENGTH']:
            log.info({
                'message': 'The user supplied an answer of length {0}, but {1} is required'.format(
                    len(answer['answer']),
                    current_app.config['ANSWERS_MINIMUM_LENGTH']
                ),
                'user': username,
            })
            raise ValidationError('The answer must be at least {0} characters long'.format(
                current_app.config['ANSWERS_MINIMUM_LENGTH']))

        # If answers aren't stored as case-sensitive, then convert it to lowercase
        if current_app.config['CASE_SENSITIVE_ANSWERS'] is False:
            log.debug({'message': 'Setting the answer to lowercase', 'user': username})
            answer['answer'] = answer['answer'].lower()

        # Make sure the supplied question_id maps to a real and enabled question in the database
        question = Question.query.get(answer['question_id'])
        if not question:
            log.info({'message': 'The user supplied an invalid question', 'user': username})
            raise ValidationError('The "question_id" is invalid')
        elif question.enabled is False:
            log.info({'message': 'The user tried to use a disabled question', 'user': username})
            raise ValidationError(
                'The "question_id" of {0} is to a disabled question'.format(question.id))

        # Store these in sets to check duplicates
        question_ids.add(answer['question_id'])
        answer_strings.add(answer['answer'])

    # Make sure the user doesn't try to reuse the same question
    if len(question_ids) != num_answers:
        log.info({'message': 'The user supplied duplicate questions', 'user': username})
        raise ValidationError(
            'One or more questions were the same. Please provide unique questions.')

    # If duplicate answers aren't allowed, then verify the answers are unique
    allow_dup_answers = current_app.config['ALLOW_DUPLICATE_ANSWERS']
    if allow_dup_answers is False and num_answers != len(answer_strings):
        log.info({'message': 'The user supplied duplicate answers', 'user': username})
        raise ValidationError('One or more answers were the same. Please provide unique answers.')

    # Now that the input is validated, add the entries to the database
    answer_objects = []
    for answer in req_json:
        hashed_answer = Answer.hash_answer(answer['answer'])
        answer_obj = Answer(
            answer=hashed_answer, question_id=answer['question_id'], user_id=user_id)
        db.session.add(answer_obj)
        answer_objects.append(answer_obj)
    db.session.commit()

    # This must be run after the session is committed because the ID needs to be set
    answers_json = [answer.to_json() for answer in answer_objects]
    log.info({'message': 'The user successfully set their secret answers', 'user': username})
    return jsonify(answers_json), 201


@api_v1.route('/reset', methods=['POST'])
def reset_password():
    """
    Reset a user's password using their secret answers.

    :rtype: flask.Response
    """
    req_json = request.get_json(force=True)
    _validate_api_input(req_json, 'answers', list)
    _validate_api_input(req_json, 'new_password', string_types)
    _validate_api_input(req_json, 'username', string_types)
    answers = req_json['answers']
    new_password = req_json['new_password']
    username = req_json['username']

    not_setup_msg = ('You must have configured at least {0} secret answers before resetting your '
                     'password').format(current_app.config['REQUIRED_ANSWERS'])
    # Verify the user exists in the database
    ad = adreset.ad.AD()
    ad.service_account_login()
    user_id = User.get_id_from_ad_username(username, ad)
    if not user_id:
        msg = 'The user attempted a password reset but does not exist in the database'
        log.debug({'message': msg, 'user': username})
        raise ValidationError(not_setup_msg)

    # Make sure the user isn't locked out
    if User.is_user_locked_out(user_id):
        msg = 'The user attempted a password reset but their account is locked in ADReset'
        log.info({'message': msg, 'user': username})
        raise Unauthorized('Your account is locked. Please try again later.')

    db_answers = Answer.query.filter_by(user_id=user_id).all()
    # Create a dictionary of question_id to answer from entries in the database. This will avoid
    # the need to continuously loop through these answers looking for specific answers later on.
    q_id_to_answer_db = {}
    for answer in db_answers:
        q_id_to_answer_db[answer.question_id] = answer.answer

    # Make sure the user has all their answers configured
    if len(q_id_to_answer_db.keys()) != current_app.config['REQUIRED_ANSWERS']:
        msg = ('The user did not have their secret answers configured and attempted to reset their '
               'password')
        log.debug({'message': msg, 'user': username})
        raise ValidationError(not_setup_msg)

    seen_question_ids = set()
    for answer in answers:
        if not isinstance(answer, dict) or 'question_id' not in answer or 'answer' not in answer:
            raise ValidationError(
                'The answers must be an object with the keys "question_id" and "answer"')
        _validate_api_input(answer, 'question_id', int)
        _validate_api_input(answer, 'answer', string_types)

        if answer['question_id'] not in q_id_to_answer_db:
            msg = ('The user answered a question they did not previously configure while '
                   'attempting to reset their password')
            log.info({'message': msg, 'user': username})
            raise ValidationError(
                'One of the answers was to a question that wasn\'t previously configured')
        # Don't allow an attacker to enter in the same question and answer combination more than
        # once
        if answer['question_id'] in seen_question_ids:
            msg = ('The user answered the same question multiple times while attempting to reset '
                   'their password')
            log.info({'message': msg, 'user': username})
            raise ValidationError('You must answer {0} different questions'.format(
                current_app.config['REQUIRED_ANSWERS']))
        seen_question_ids.add(answer['question_id'])

    # Only check if the answers are correct after knowing the input is valid as to not give away
    # any hints as to which answer is incorrect for an attacker
    for answer in answers:
        if current_app.config['CASE_SENSITIVE_ANSWERS'] is True:
            input_answer = answer['answer']
        else:
            input_answer = answer['answer'].lower()
        is_correct_answer = Answer.verify_answer(
            input_answer, q_id_to_answer_db[answer['question_id']])
        if is_correct_answer is not True:
            log.info({'message': 'The user entered an incorrect answer', 'user': username})
            failed_attempt = FailedAttempt(user_id=user_id, time=datetime.utcnow())
            db.session.add(failed_attempt)
            db.session.commit()

            if User.is_user_locked_out(user_id):
                msg = 'The user failed too many password reset attempts. They are now locked out.'
                log.info({'message': msg, 'user': username})
                raise Unauthorized('You have answered incorrectly too many times. Your account is '
                                   'now locked. Please try again later.')
            raise Unauthorized('One or more answers were incorrect. Please try again.')

    log.debug({'message': 'The user successfully answered their questions', 'user': username})
    ad.reset_password(username, new_password)
    log.info({'message': 'The user successfully reset their password', 'user': username})
    return jsonify({}), 204
