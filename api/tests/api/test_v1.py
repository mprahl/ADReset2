# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

import json
from datetime import datetime

import flask_jwt_extended
import pytest
import mock

from adreset import version
from adreset.models import User, Question, Answer, FailedAttempt, db


def test_about(client):
    """Test the /api/v1/about route."""
    rv = client.get('/api/v1/about')
    assert json.loads(rv.data.decode('utf-8')) == {
        'account_status_enabled': True,
        'allow_duplicate_answers': False,
        'answers_minimum_length': 2,
        'required_answers': 3,
        'version': version,
    }


@pytest.mark.parametrize(
    'origin, header_set', [('http://localhost', True), ('http://some-hacker.domain.local', False)]
)
def test_insert_headers(client, origin, header_set):
    """Test that the appropriate headers are inserted in a Flask response."""
    rv = client.get('/api/v1/', headers={'Origin': origin})
    if header_set:
        assert 'Access-Control-Allow-Origin: {}'.format(origin) in str(rv.headers)
        assert 'Access-Control-Allow-Headers: Content-Type' in str(rv.headers)
        assert 'Access-Control-Allow-Methods: DELETE, GET, OPTIONS, PATCH, POST' in str(rv.headers)
    else:
        assert 'Access-Control-Allow-Origin' not in str(rv.headers)
        assert 'Access-Control-Allow-Headers' not in str(rv.headers)
        assert 'Access-Control-Allow-Methods' not in str(rv.headers)


def test_login(client, mock_user_ad):
    """Test that logins are successfull."""
    # Make sure the user doesn't exist before the first login
    assert len(User.query.all()) == 0
    # Because we are mocking AD with ldap3, we have to use the distinguished name to log in
    rv = client.post(
        '/api/v1/login',
        data=json.dumps(
            {'username': 'CN=testuser2,OU=ADReset,DC=adreset,DC=local', 'password': 'P@ssW0rd'}
        ),
    )
    assert rv.status_code == 200
    rv_json = json.loads(rv.data.decode('utf-8'))
    assert set(rv_json.keys()) == set(['token'])
    # Make sure the user was created after the first login
    guid = '10385a23-6def-4990-84a8-32444e36e496'
    assert User.query.filter_by(ad_guid=guid).first()
    decoded_token = flask_jwt_extended.decode_token(rv_json['token'])
    assert decoded_token['sub']['guid'] == guid
    assert decoded_token['sub']['username'] == 'testuser2'
    assert decoded_token['user_claims']['roles'] == ['user']


def test_login_failed_not_enough_questions(client, mock_user_ad):
    """Test that the login fails when there aren't enough questions configured."""
    # There should be three questions by default, so just delete one so that an error is generated
    first_question = Question.query.get(1)
    db.session.delete(first_question)
    db.session.commit()
    # Because we are mocking AD with ldap3, we have to use the distinguished name to log in
    rv = client.post(
        '/api/v1/login',
        data=json.dumps(
            {'username': 'CN=testuser2,OU=ADReset,DC=adreset,DC=local', 'password': 'P@ssW0rd'}
        ),
    )
    assert rv.status_code == 400
    rv_json = json.loads(rv.data.decode('utf-8'))
    assert rv_json['message'] == 'The administrator has not finished configuring the application'


def test_admin_login(client, mock_admin_ad):
    """Test that admin logins are successfull."""
    # Make sure the user doesn't exist before the first login
    assert len(User.query.all()) == 0
    # Because we are mocking AD with ldap3, we have to use the distinguished name to log in
    rv = client.post(
        '/api/v1/login',
        data=json.dumps(
            {'username': 'CN=testuser,OU=ADReset,DC=adreset,DC=local', 'password': 'P@ssW0rd'}
        ),
    )
    assert rv.status_code == 200
    rv_json = json.loads(rv.data.decode('utf-8'))
    assert set(rv_json.keys()) == set(['token'])
    # Make sure the user was created after the first login
    guid = '5609c5ec-c0df-4480-a94b-b6eb0fc4c066'
    assert User.query.filter_by(ad_guid=guid).first()
    decoded_token = flask_jwt_extended.decode_token(rv_json['token'])
    assert decoded_token['sub']['guid'] == guid
    assert decoded_token['sub']['username'] == 'testuser'
    assert decoded_token['user_claims']['roles'] == ['admin']


def test_logout(client, logged_in_headers):
    """Test that logouts are successfull."""
    rv = client.post('/api/v1/logout', headers=logged_in_headers)
    assert rv.status_code == 200
    rv_json = json.loads(rv.data.decode('utf-8'))
    assert rv_json['message'] == 'You were logged out successfully'

    # Make sure that if the user tries to log out with the same token they get an error
    # saying their token is revoked
    rv = client.post('/api/v1/logout', headers=logged_in_headers)
    assert rv.status_code == 401
    rv_json = json.loads(rv.data.decode('utf-8'))
    assert rv_json['message'] == 'Token has been revoked'


def test_add_question(client, logged_in_headers, admin_logged_in_headers):
    """Test the /api/v1/questions POST route."""
    data = json.dumps({'question': 'What is your favorite movie?'})
    rv = client.post('/api/v1/questions', headers=admin_logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'enabled': True,
        'id': 4,
        'question': 'What is your favorite movie?',
        'url': 'http://localhost/api/v1/questions/4',
    }

    rv = client.post('/api/v1/questions', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'You must be an administrator to proceed with this action',
        'status': 403,
    }


def test_add_question_disabled(client, admin_logged_in_headers):
    """Test the /api/v1/questions POST route with "enabled" set to false."""
    data = json.dumps({'enabled': False, 'question': 'What is your favorite movie?'})
    rv = client.post('/api/v1/questions', headers=admin_logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'enabled': False,
        'id': 4,
        'question': 'What is your favorite movie?',
        'url': 'http://localhost/api/v1/questions/4',
    }


def test_patch_question(client, logged_in_headers, admin_logged_in_headers):
    """Test the /api/v1/questions PATCH route."""
    data = json.dumps({'question': 'What is your favorite movie?', 'enabled': False})
    rv = client.patch('/api/v1/questions/1', headers=admin_logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'enabled': False,
        'id': 1,
        'question': 'What is your favorite movie?',
        'url': 'http://localhost/api/v1/questions/1',
    }

    rv = client.patch('/api/v1/questions/1', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'You must be an administrator to proceed with this action',
        'status': 403,
    }


@pytest.mark.parametrize('enabled', (True, False, None))
def test_get_questions(enabled, client):
    """Test the /api/v1/questions route."""
    question = Question(question='What is your favorite type of pizza?', enabled=False)
    db.session.add(question)
    db.session.commit()

    url = '/api/v1/questions'
    if enabled is True:
        url += '?enabled=true'
    elif enabled is False:
        url += '?enabled=false'

    items = []
    if enabled in (None, True):
        items += [
            {
                'enabled': True,
                'id': 1,
                'question': 'What is your favorite flavor of ice cream?',
                'url': 'http://localhost/api/v1/questions/1',
            },
            {
                'enabled': True,
                'id': 2,
                'question': 'What is your favorite color?',
                'url': 'http://localhost/api/v1/questions/2',
            },
            {
                'enabled': True,
                'id': 3,
                'question': 'What is your favorite toy?',
                'url': 'http://localhost/api/v1/questions/3',
            },
        ]

    if enabled in (None, False):
        items += [
            {
                'enabled': False,
                'id': 4,
                'question': 'What is your favorite type of pizza?',
                'url': 'http://localhost/api/v1/questions/4',
            }
        ]

    rv = client.get(url, headers={'Content-Type': 'application/json'})
    data = json.loads(rv.data.decode('utf-8'))
    assert data['items'] == items
    # Order of the query arguments can vary
    assert data['meta']['first']
    assert data['meta']['last']
    assert data['meta']['next'] is None
    assert data['meta']['page'] == 1
    assert data['meta']['pages'] == 1
    assert data['meta']['per_page'] == 10
    assert data['meta']['previous'] is None
    assert data['meta']['total'] == len(items)


def test_get_question(client):
    """Test the /api/v1/questions/<id> route."""
    rv = client.get('/api/v1/questions/2', headers={'Content-Type': 'application/json'})
    assert json.loads(rv.data.decode('utf-8')) == {
        'enabled': True,
        'id': 2,
        'question': 'What is your favorite color?',
    }


def test_add_answers(client, logged_in_headers, admin_logged_in_headers):
    """Test the answers POST route."""
    data = json.dumps(
        [
            {'question_id': 3, 'answer': 'Buzz Lightyear'},
            {'question_id': 1, 'answer': 'strawberry'},
            {'question_id': 2, 'answer': 'bright pink'},
        ]
    )
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == [
        {
            'id': 1,
            'question': {
                'enabled': True,
                'id': 3,
                'question': 'What is your favorite toy?',
                'url': 'http://localhost/api/v1/questions/3',
            },
            'url': 'http://localhost/api/v1/answers/1',
            'user_id': 1,
        },
        {
            'id': 2,
            'question': {
                'enabled': True,
                'id': 1,
                'question': 'What is your favorite flavor of ice cream?',
                'url': 'http://localhost/api/v1/questions/1',
            },
            'url': 'http://localhost/api/v1/answers/2',
            'user_id': 1,
        },
        {
            'id': 3,
            'question': {
                'enabled': True,
                'id': 2,
                'question': 'What is your favorite color?',
                'url': 'http://localhost/api/v1/questions/2',
            },
            'url': 'http://localhost/api/v1/answers/3',
            'user_id': 1,
        },
    ]

    rv = client.post('/api/v1/answers', headers=admin_logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'Administrators are not authorized to proceed with this action',
        'status': 403,
    }


def test_add_answers_duplicate_question(client, logged_in_headers):
    """Test that the answers POST route errors when a duplicate question is provided."""
    data = json.dumps(
        [
            {'question_id': 3, 'answer': 'Buzz Lightyear'},
            {'question_id': 2, 'answer': 'cherry red'},
            {'question_id': 2, 'answer': 'bright pink'},
        ]
    )
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'One or more questions were the same. Please provide unique questions.',
        'status': 400,
    }


def test_add_answers_disabled_question(client, logged_in_headers):
    """Test that the answers POST route errors when a question is disabled."""
    question = Question.query.get(2)
    question.enabled = False
    db.session.add(question)
    db.session.commit()
    data = json.dumps(
        [
            {'question_id': 3, 'answer': 'Buzz Lightyear'},
            {'question_id': 1, 'answer': 'strawberry'},
            {'question_id': 2, 'answer': 'bright pink'},
        ]
    )
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'The "question_id" of 2 is to a disabled question',
        'status': 400,
    }


def test_add_answers_duplicate_answer(app, client, logged_in_headers):
    """Test that the answers POST route errors when an answer is reused."""
    data = json.dumps(
        [
            {'question_id': 3, 'answer': 'Buzz Lightyear'},
            {'question_id': 1, 'answer': 'strawberry'},
            {'question_id': 2, 'answer': 'strawberry'},
        ]
    )
    with mock.patch.dict(app.config, {'ALLOW_DUPLICATE_ANSWERS': False}):
        rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'One or more answers were the same. Please provide unique answers.',
        'status': 400,
    }


def test_add_answers_duplicate_answer_conf_true(app, client, logged_in_headers):
    """Test that the answers POST route allows an answer to be reused with the config as true."""
    data = json.dumps(
        [
            {'question_id': 3, 'answer': 'Buzz Lightyear'},
            {'question_id': 1, 'answer': 'strawberry'},
            {'question_id': 2, 'answer': 'bright pink'},
        ]
    )
    with mock.patch.dict(app.config, {'ALLOW_DUPLICATE_ANSWERS': True}):
        rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert rv.status_code == 201


def test_add_answers_past_limit(client, logged_in_headers):
    """Test that the answers POST route doesn't allow a fourth answer for a user."""
    # Add a fourth question so that a question doesn't have to be reused for the POST request
    question = Question(question='Where were you born?')
    db.session.add(question)
    db.session.commit()
    data = json.dumps(
        [
            {'question_id': 3, 'answer': 'Buzz Lightyear'},
            {'question_id': 1, 'answer': 'strawberry'},
            {'question_id': 2, 'answer': 'bright pink'},
            {'question_id': 4, 'answer': 'Boston, MA'},
        ]
    )
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': '4 answers were supplied but 3 are required',
        'status': 400,
    }


def test_add_answers_under_limit(client, logged_in_headers):
    """Test that the answers POST route doesn't allow less than the required amount of answers."""
    data = json.dumps([{'question_id': 3, 'answer': 'Buzz Lightyear'}])
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': '1 answer was supplied but 3 are required',
        'status': 400,
    }


def test_add_answers_case_insensitive(app, client, logged_in_headers):
    """Test the answers POST route when case sensitive answers are disabled."""
    data = json.dumps(
        [
            {'question_id': 2, 'answer': 'Bright Green'},
            {'question_id': 3, 'answer': 'Buzz Lightyear'},
            {'question_id': 1, 'answer': 'strawberry'},
        ]
    )
    with mock.patch.dict(app.config, {'CASE_SENSITIVE_ANSWERS': False}):
        client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert Answer.verify_answer('bright green', Answer.query.get(1).answer) is True
    assert Answer.verify_answer('Bright Green', Answer.query.get(1).answer) is False


def test_add_answers_case_sensitive(app, client, logged_in_headers):
    """Test the answers POST route when case sensitive answers are enabled."""
    data = json.dumps(
        [
            {'question_id': 2, 'answer': 'Bright Green'},
            {'question_id': 3, 'answer': 'Buzz Lightyear'},
            {'question_id': 1, 'answer': 'strawberry'},
        ]
    )
    with mock.patch.dict(app.config, {'CASE_SENSITIVE_ANSWERS': True}):
        client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert Answer.verify_answer('bright green', Answer.query.get(1).answer) is False
    assert Answer.verify_answer('Bright Green', Answer.query.get(1).answer) is True


def test_add_answers_not_min_length(client, logged_in_headers):
    """Test that the answers POST route doesn't allow an answer that is too short."""
    data = json.dumps(
        [
            {'question_id': 2, 'answer': 'b'},
            {'question_id': 3, 'answer': 'Buzz Lightyear'},
            {'question_id': 1, 'answer': 'strawberry'},
        ]
    )
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'The answer must be at least 2 characters long',
        'status': 400,
    }


def test_add_answers_no_question_id(client, logged_in_headers):
    """Test that the answers POST route doesn't allow an answer without a question_id."""
    data = json.dumps(
        [
            {'answer': 'not sure'},
            {'question_id': 3, 'answer': 'Buzz Lightyear'},
            {'question_id': 1, 'answer': 'strawberry'},
        ]
    )
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'The parameter "question_id" must not be empty',
        'status': 400,
    }


def test_add_answers_invalid_question_id(client, logged_in_headers):
    """Test that the answers POST route doesn't allow an answer with an invalid question_id."""
    data = json.dumps(
        [
            {'question_id': 123, 'answer': 'Buzz Lightyear'},
            {'question_id': 1, 'answer': 'strawberry'},
            {'question_id': 2, 'answer': 'bright pink'},
        ]
    )
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'The "question_id" is invalid',
        'status': 400,
    }


def test_get_answer(client, logged_in_headers, admin_logged_in_headers):
    """Test the answers/<id> route."""
    answer = Answer(answer=Answer.hash_answer('strawberry'), user_id=1, question_id=1)
    db.session.add(answer)
    db.session.commit()
    rv = client.get('/api/v1/answers/1', headers=logged_in_headers)
    assert json.loads(rv.data.decode('utf-8')) == {
        'id': 1,
        'question': {
            'enabled': True,
            'id': 1,
            'question': 'What is your favorite flavor of ice cream?',
            'url': 'http://localhost/api/v1/questions/1',
        },
        'user_id': 1,
    }

    rv = client.get('/api/v1/answers/1', headers=admin_logged_in_headers)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'Administrators are not authorized to proceed with this action',
        'status': 403,
    }


def test_get_answer_not_found(client, logged_in_headers):
    """Test getting a non-existent answer using the answers/<id> route."""
    rv = client.get('/api/v1/answers/1', headers=logged_in_headers)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'The answer was not found',
        'status': 404,
    }


def test_get_answer_different_user(client, logged_in_headers):
    """Test accessing the answer of a different user in the answers/<id> route."""
    user = User(ad_guid='5609c5ec-c0df-4480-a94b-b6eb0fc4c066')
    db.session.add(user)
    db.session.commit()
    answer = Answer(answer=Answer.hash_answer('strawberry'), user_id=user.id, question_id=1)
    db.session.add(answer)
    db.session.commit()
    rv = client.get('/api/v1/answers/1', headers=logged_in_headers)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'This answer is not associated with your account',
        'status': 401,
    }


def test_get_answers(client, logged_in_headers, admin_logged_in_headers):
    """Test the answers route."""
    answer = Answer(answer=Answer.hash_answer('strawberry'), user_id=1, question_id=1)
    answer2 = Answer(answer=Answer.hash_answer('green'), user_id=1, question_id=2)
    answer3 = Answer(answer=Answer.hash_answer('Buzz Lightyear'), user_id=1, question_id=3)
    answer4 = Answer(answer=Answer.hash_answer('Hamm'), user_id=2, question_id=3)
    db.session.add(answer)
    db.session.add(answer2)
    db.session.add(answer3)
    db.session.add(answer4)
    db.session.commit()
    rv = client.get('/api/v1/answers', headers=logged_in_headers)
    items = [
        {
            'id': 1,
            'question': {
                'enabled': True,
                'id': 1,
                'question': 'What is your favorite flavor of ice cream?',
                'url': 'http://localhost/api/v1/questions/1',
            },
            'url': 'http://localhost/api/v1/answers/1',
            'user_id': 1,
        },
        {
            'id': 2,
            'question': {
                'enabled': True,
                'id': 2,
                'question': 'What is your favorite color?',
                'url': 'http://localhost/api/v1/questions/2',
            },
            'url': 'http://localhost/api/v1/answers/2',
            'user_id': 1,
        },
        {
            'id': 3,
            'question': {
                'enabled': True,
                'id': 3,
                'question': 'What is your favorite toy?',
                'url': 'http://localhost/api/v1/questions/3',
            },
            'url': 'http://localhost/api/v1/answers/3',
            'user_id': 1,
        },
    ]
    assert json.loads(rv.data.decode('utf-8'))['items'] == items

    rv = client.get('/api/v1/answers', headers=admin_logged_in_headers)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'Administrators are not authorized to proceed with this action',
        'status': 403,
    }


# logged_in_headers isn't directly used but it causes the user entry to be created in the DB
def test_get_answers_unauthenticated(client, logged_in_headers, mock_ad):
    """Test the unauthenticated answers route."""
    answer = Answer(answer=Answer.hash_answer('strawberry'), user_id=1, question_id=1)
    answer2 = Answer(answer=Answer.hash_answer('green'), user_id=1, question_id=2)
    answer3 = Answer(answer=Answer.hash_answer('Buzz Lightyear'), user_id=1, question_id=3)
    answer4 = Answer(answer=Answer.hash_answer('Hamm'), user_id=2, question_id=3)
    db.session.add(answer)
    db.session.add(answer2)
    db.session.add(answer3)
    db.session.add(answer4)
    db.session.commit()
    rv = client.get('/api/v1/answers/testuser2', headers={'Content-Type': 'application/json'})
    items = [
        {
            'id': 1,
            'question': {
                'enabled': True,
                'id': 1,
                'question': 'What is your favorite flavor of ice cream?',
                'url': 'http://localhost/api/v1/questions/1',
            },
            'url': 'http://localhost/api/v1/answers/1',
            'user_id': 1,
        },
        {
            'id': 2,
            'question': {
                'enabled': True,
                'id': 2,
                'question': 'What is your favorite color?',
                'url': 'http://localhost/api/v1/questions/2',
            },
            'url': 'http://localhost/api/v1/answers/2',
            'user_id': 1,
        },
        {
            'id': 3,
            'question': {
                'enabled': True,
                'id': 3,
                'question': 'What is your favorite toy?',
                'url': 'http://localhost/api/v1/questions/3',
            },
            'url': 'http://localhost/api/v1/answers/3',
            'user_id': 1,
        },
    ]
    assert json.loads(rv.data.decode('utf-8'))['items'] == items


def test_delete_answers(client, logged_in_headers, admin_logged_in_headers):
    """Test the answers route using the DELETE method to reset the user's configured answers."""
    answer = Answer(answer=Answer.hash_answer('strawberry'), user_id=1, question_id=1)
    answer2 = Answer(answer=Answer.hash_answer('green'), user_id=1, question_id=2)
    answer3 = Answer(answer=Answer.hash_answer('Buzz Lightyear'), user_id=1, question_id=3)
    db.session.add(answer)
    db.session.add(answer2)
    db.session.add(answer3)
    db.session.commit()
    rv = client.delete('/api/v1/answers', headers=logged_in_headers)
    assert rv.status_code == 204
    assert rv.data.decode('utf-8') == ''
    assert len(Answer.query.filter_by(user_id=1).all()) == 0

    rv = client.delete('/api/v1/answers', headers=admin_logged_in_headers)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'Administrators are not authorized to proceed with this action',
        'status': 403,
    }


def _configure_user():
    """Configure testuser2 in the database."""
    user = User(ad_guid='10385a23-6def-4990-84a8-32444e36e496')
    db.session.add(user)
    answer = Answer(answer=Answer.hash_answer('strawberry'), user_id=1, question_id=1)
    answer2 = Answer(answer=Answer.hash_answer('green'), user_id=1, question_id=2)
    answer3 = Answer(answer=Answer.hash_answer('buzz lightyear'), user_id=1, question_id=3)
    db.session.add(answer)
    db.session.add(answer2)
    db.session.add(answer3)
    db.session.commit()


_reset_data = json.dumps(
    {
        'answers': [
            {'question_id': 1, 'answer': 'strawberry'},
            {'question_id': 2, 'answer': 'green'},
            {'question_id': 3, 'answer': 'buzz lightyear'},
        ],
        'new_password': 'RedSoxWorldSeriesCh@mps',
        'username': 'testuser2',
    }
)


def test_reset(client, mock_ad):
    """Test the reset route when the user is properly configured."""
    _configure_user()
    headers = {'Content-Type': 'application/json'}
    rv = client.post('/api/v1/reset', headers=headers, data=_reset_data)
    assert rv.status_code == 204
    assert rv.data.decode('utf-8') == ''


def test_reset_no_user_in_ad(client, mock_ad):
    """Test the reset route on a user that does not exist in Active Directory."""
    headers = {'Content-Type': 'application/json'}
    reset_data = json.loads(_reset_data)
    reset_data['username'] = 'nonexistent_user'
    reset_data = json.dumps(reset_data)
    rv = client.post('/api/v1/reset', headers=headers, data=reset_data)
    assert rv.status_code == 400
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': (
            'You must have configured at least 3 secret answers before resetting your ' 'password'
        ),
        'status': 400,
    }


def test_reset_no_user_in_db(client, mock_ad):
    """Test the reset route on a user that does not exist in the database."""
    headers = {'Content-Type': 'application/json'}
    rv = client.post('/api/v1/reset', headers=headers, data=_reset_data)
    assert rv.status_code == 400
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': (
            'You must have configured at least 3 secret answers before resetting your ' 'password'
        ),
        'status': 400,
    }


def test_reset_locked_out(client, mock_ad):
    """Test the reset route on a user that is locked out."""
    _configure_user()
    for _ in range(3):
        db.session.add(FailedAttempt(user_id=1, time=datetime.utcnow()))
    db.session.commit()
    headers = {'Content-Type': 'application/json'}
    rv = client.post('/api/v1/reset', headers=headers, data=_reset_data)
    assert rv.status_code == 401
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'Your account is locked. Please try again later.',
        'status': 401,
    }


def test_reset_gets_locked_out(client, mock_ad):
    """Test the reset route when a user gets locked out."""
    _configure_user()
    for _ in range(2):
        db.session.add(FailedAttempt(user_id=1, time=datetime.utcnow()))
    db.session.commit()
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(
        {
            'answers': [
                {'question_id': 1, 'answer': 'wrong'},
                {'question_id': 2, 'answer': 'green'},
                {'question_id': 3, 'answer': 'buzz lightyear'},
            ],
            'new_password': 'RedSoxWorldSeriesCh@mps',
            'username': 'testuser2',
        }
    )
    rv = client.post('/api/v1/reset', headers=headers, data=data)
    assert rv.status_code == 401
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': (
            'You have answered incorrectly too many times. Your account is now locked. '
            'Please try again later.'
        ),
        'status': 401,
    }


def test_reset_not_enough_configured_answers(client, mock_ad):
    """Test the reset route on a user that does not have enough secret answers configured."""
    _configure_user()
    db.session.delete(Answer.query.first())
    db.session.commit()
    headers = {'Content-Type': 'application/json'}
    rv = client.post('/api/v1/reset', headers=headers, data=_reset_data)
    assert rv.status_code == 400
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': (
            'You must have configured at least 3 secret answers before resetting your ' 'password'
        ),
        'status': 400,
    }


def test_reset_invalid_question_id(client, mock_ad):
    """Test the reset route when the user answers a question they don't have configured."""
    _configure_user()
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(
        {
            'answers': [
                {'question_id': 999, 'answer': 'strawberry'},
                {'question_id': 2, 'answer': 'green'},
                {'question_id': 3, 'answer': 'buzz lightyear'},
            ],
            'new_password': 'RedSoxWorldSeriesCh@mps',
            'username': 'testuser2',
        }
    )
    rv = client.post('/api/v1/reset', headers=headers, data=data)
    assert rv.status_code == 400
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'One of the answers was to a question that wasn\'t previously configured',
        'status': 400,
    }


def test_reset_same_question(client, mock_ad):
    """Test the reset route when the user answers the same question multiple times."""
    _configure_user()
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(
        {
            'answers': [
                {'question_id': 1, 'answer': 'strawberry'},
                {'question_id': 1, 'answer': 'strawberry'},
                {'question_id': 3, 'answer': 'buzz lightyear'},
            ],
            'new_password': 'RedSoxWorldSeriesCh@mps',
            'username': 'testuser2',
        }
    )
    rv = client.post('/api/v1/reset', headers=headers, data=data)
    assert rv.status_code == 400
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'You must answer 3 different questions',
        'status': 400,
    }


def test_reset_incorrect_answer(client, mock_ad):
    """Test the reset route when the user answers a question incorrectly."""
    _configure_user()
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(
        {
            'answers': [
                {'question_id': 1, 'answer': 'strawberry'},
                {'question_id': 2, 'answer': 'I dunno'},
                {'question_id': 3, 'answer': 'buzz lightyear'},
            ],
            'new_password': 'RedSoxWorldSeriesCh@mps',
            'username': 'testuser2',
        }
    )
    rv = client.post('/api/v1/reset', headers=headers, data=data)
    assert rv.status_code == 401
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'One or more answers were incorrect. Please try again.',
        'status': 401,
    }


def test_account_status(client, mock_ad):
    """Test the account-status route."""
    rv = client.get('/api/v1/account-status/lockeduser')
    assert rv.status_code == 200
    assert json.loads(rv.data.decode('utf-8')) == {
        'account_is_disabled': False,
        'account_is_locked_out': True,
        'account_is_unlocked_on': '2079-09-13T18:29:01+0000',
        'password_can_be_set_on': None,
        'password_expires_on': None,
        'password_last_set_on': '2016-10-31T23:03:11+0000',
        'password_never_expires': True,
    }


def test_account_status_disabled(app, client, mock_ad):
    """Test that the account-status route returns a 404 when disabled."""
    with mock.patch.dict(app.config, {'ACCOUNT_STATUS_ENABLED': False}):
        rv = client.get('/api/v1/account-status/lockeduser')
    assert rv.status_code == 404
