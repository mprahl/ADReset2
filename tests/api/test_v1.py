# SPDX-License-Identifier: GPL-3.0+

from __future__ import unicode_literals

import json

import flask_jwt_extended

from adreset import version
from adreset.models import User, Question, Answer, db


def test_about(client):
    """Test the /api/v1/about route."""
    rv = client.get('/api/v1/about')
    assert json.loads(rv.data.decode('utf-8')) == {'version': version}


def test_insert_headers(client):
    """Test that the appropriate headers are inserted in a Flask response."""
    rv = client.get('/api/v1/')
    assert 'Access-Control-Allow-Origin: *' in str(rv.headers)
    assert 'Access-Control-Allow-Headers: Content-Type' in str(rv.headers)
    assert 'Access-Control-Allow-Methods: GET, POST, OPTIONS' in str(rv.headers)


def test_login(client, mock_user_ad):
    """Test that logins are successfull."""
    # Make sure the user doesn't exist before the first login
    assert len(User.query.all()) == 0
    # Because we are mocking AD with ldap3, we have to use the distinguished name to log in
    rv = client.post('/api/v1/login', data=json.dumps({
        'username': 'CN=testuser2,OU=ADReset,DC=adreset,DC=local',
        'password': 'P@ssW0rd'}))
    assert rv.status_code == 200
    rv_json = json.loads(rv.data.decode('utf-8'))
    assert set(rv_json.keys()) == set(['token'])
    # Make sure the user was created after the first login
    guid = '10385a23-6def-4990-84a8-32444e36e496'
    assert User.query.filter_by(ad_guid=guid).first()
    decoded_token = flask_jwt_extended.decode_token(rv_json['token'])
    assert decoded_token['sub'] == guid
    assert decoded_token['user_claims']['roles'] == ['user']


def test_login_failed_not_enough_questions(client, mock_user_ad):
    """Test that the login fails when there aren't enough questions configured."""
    # There should be three questions by default, so just delete one so that an error is generated
    first_question = Question.query.get(1)
    db.session.delete(first_question)
    db.session.commit()
    # Because we are mocking AD with ldap3, we have to use the distinguished name to log in
    rv = client.post('/api/v1/login', data=json.dumps({
        'username': 'CN=testuser2,OU=ADReset,DC=adreset,DC=local',
        'password': 'P@ssW0rd'}))
    assert rv.status_code == 400
    rv_json = json.loads(rv.data.decode('utf-8'))
    assert rv_json['message'] == 'The administrator has not finished configuring the application'


def test_admin_login(client, mock_admin_ad):
    """Test that admin logins are successfull."""
    # Make sure the user doesn't exist before the first login
    assert len(User.query.all()) == 0
    # Because we are mocking AD with ldap3, we have to use the distinguished name to log in
    rv = client.post('/api/v1/login', data=json.dumps({
        'username': 'CN=testuser,OU=ADReset,DC=adreset,DC=local',
        'password': 'P@ssW0rd'}))
    assert rv.status_code == 200
    rv_json = json.loads(rv.data.decode('utf-8'))
    assert set(rv_json.keys()) == set(['token'])
    # Make sure the user was created after the first login
    guid = '5609c5ec-c0df-4480-a94b-b6eb0fc4c066'
    assert User.query.filter_by(ad_guid=guid).first()
    decoded_token = flask_jwt_extended.decode_token(rv_json['token'])
    assert decoded_token['sub'] == guid
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
    data = json.dumps({
        'question': 'What is your favorite movie?'
    })
    rv = client.post('/api/v1/questions', headers=admin_logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'id': 4,
        'question': 'What is your favorite movie?',
        'url': 'http://localhost/api/v1/questions/4'
    }

    rv = client.post('/api/v1/questions', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'You must be an administrator to proceed with this action',
        'status': 403
    }


def test_get_questions(client):
    """Test the /api/v1/questions route."""
    rv = client.get('/api/v1/questions', headers={'Content-Type': 'application/json'})
    items = [
        {
            'id': 1,
            'question': 'What is your favorite flavor of ice cream?',
            'url': 'http://localhost/api/v1/questions/1'
        },
        {
            'id': 2,
            'question': 'What is your favorite color?',
            'url': 'http://localhost/api/v1/questions/2'
        },
        {
            'id': 3,
            'question': 'What is your favorite toy?',
            'url': 'http://localhost/api/v1/questions/3'
        }
    ]
    data = json.loads(rv.data.decode('utf-8'))
    assert data['items'] == items
    # Order of the query arguments can vary
    assert data['meta']['first'] in ('http://localhost/api/v1/questions?page=1&per_page=10',
                                     'http://localhost/api/v1/questions?per_page=10&page=1')
    assert data['meta']['last'] in ('http://localhost/api/v1/questions?page=1&per_page=10',
                                    'http://localhost/api/v1/questions?per_page=10&page=1')
    assert data['meta']['next'] is None
    assert data['meta']['page'] == 1
    assert data['meta']['pages'] == 1
    assert data['meta']['per_page'] == 10
    assert data['meta']['previous'] is None
    assert data['meta']['total'] == 3


def test_get_question(client):
    """Test the /api/v1/questions/<id> route."""
    rv = client.get('/api/v1/questions/2', headers={'Content-Type': 'application/json'})
    assert json.loads(rv.data.decode('utf-8')) == {
        'id': 2,
        'question': 'What is your favorite color?'
    }


def test_add_answer(client, logged_in_headers, admin_logged_in_headers):
    """Test the answers POST route."""
    data = json.dumps({
        'question_id': 2,
        'answer': 'bright pink'
    })
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'id': 1,
        'question_id': 2,
        'url': 'http://localhost/api/v1/answers/1',
        'user_id': 1
    }

    rv = client.post('/api/v1/answers', headers=admin_logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'Administrators are not authorized to proceed with this action',
        'status': 403
    }


def test_add_answer_already_used_question(client, logged_in_headers):
    """Test that the answers POST route errors when a question is reused."""
    answer = Answer(answer=Answer.hash_answer('bright pink'), user_id=1, question_id=2)
    db.session.add(answer)
    db.session.commit()
    data = json.dumps({
        'question_id': 2,
        'answer': 'cherry red'
    })
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'That question has already been used by you',
        'status': 400
    }


def test_add_answer_already_used_answer(app, client, logged_in_headers):
    """Test that the answers POST route errors when an answer is reused."""
    app.config['ALLOW_DUPLICATE_ANSWERS'] = False
    answer = Answer(answer=Answer.hash_answer('bright pink'), user_id=1, question_id=2)
    db.session.add(answer)
    db.session.commit()
    data = json.dumps({
        'question_id': 3,
        'answer': 'bright pink'
    })
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'The supplied answer has already been used for another question',
        'status': 400
    }


def test_add_answer_already_used_answer_conf_true(app, client, logged_in_headers):
    """Test that the answers POST route allows an answer to be reused with config true."""
    app.config['ALLOW_DUPLICATE_ANSWERS'] = True
    answer = Answer(answer=Answer.hash_answer('bright pink'), user_id=1, question_id=2)
    db.session.add(answer)
    db.session.commit()
    data = json.dumps({
        'question_id': 3,
        'answer': 'bright pink'
    })
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'id': 2,
        'question_id': 3,
        'url': 'http://localhost/api/v1/answers/2',
        'user_id': 1
    }


def test_add_answer_past_limit(client, logged_in_headers):
    """Test that the answers POST route doesn't allow a fourth answer for a user."""
    answer = Answer(answer=Answer.hash_answer('strawberry'), user_id=1, question_id=1)
    answer2 = Answer(answer=Answer.hash_answer('green'), user_id=1, question_id=2)
    answer3 = Answer(answer=Answer.hash_answer('Buzz Lightyear'), user_id=1, question_id=3)
    db.session.add(answer)
    db.session.add(answer2)
    db.session.add(answer3)
    # Add a fourth question so that a question doesn't have to be reused for the POST request
    question = Question(question='Where were you born?')
    db.session.add(question)
    data = json.dumps({
        'question_id': 4,
        'answer': 'Boston, MA'
    })
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'You\'ve already set the required amount of secret answers',
        'status': 400
    }


def test_add_answer_case_insensitive(app, client, logged_in_headers):
    """Test the answers POST route when case sensitive answers are disabled."""
    app.config['CASE_SENSITIVE_ANSWERS'] = False
    data = json.dumps({
        'question_id': 2,
        'answer': 'Bright Green'
    })
    client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert Answer.verify_answer('bright green', Answer.query.get(1).answer) is True
    assert Answer.verify_answer('Bright Green', Answer.query.get(1).answer) is False


def test_add_answer_case_sensitive(app, client, logged_in_headers):
    """Test the answers POST route when case sensitive answers are enabled."""
    app.config['CASE_SENSITIVE_ANSWERS'] = True
    data = json.dumps({
        'question_id': 2,
        'answer': 'Bright Green'
    })
    client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert Answer.verify_answer('bright green', Answer.query.get(1).answer) is False
    assert Answer.verify_answer('Bright Green', Answer.query.get(1).answer) is True


def test_add_answer_not_min_length(client, logged_in_headers):
    """Test that the answers POST route doesn't allow an answer that is too short."""
    data = json.dumps({
        'question_id': 2,
        'answer': 'd'
    })
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'The answer must be at least 2 characters long',
        'status': 400
    }


def test_add_answer_no_question_id(client, logged_in_headers):
    """Test that the answers POST route doesn't allow an answer without a question_id."""
    data = json.dumps({
        'answer': 'not sure'
    })
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'The parameter "question_id" must not be empty',
        'status': 400
    }


def test_add_answer_invalid_question_id(client, logged_in_headers):
    """Test that the answers POST route doesn't allow an answer with an invalid question_id."""
    data = json.dumps({
        'answer': 'not sure',
        'question_id': 12345
    })
    rv = client.post('/api/v1/answers', headers=logged_in_headers, data=data)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'The "question_id" is invalid',
        'status': 400
    }


def test_get_answer(client, logged_in_headers, admin_logged_in_headers):
    """Test the answers/<id> route."""
    answer = Answer(answer=Answer.hash_answer('strawberry'), user_id=1, question_id=1)
    db.session.add(answer)
    db.session.commit()
    rv = client.get('/api/v1/answers/1', headers=logged_in_headers)
    assert json.loads(rv.data.decode('utf-8')) == {
        'id': 1,
        'question_id': 1,
        'user_id': 1
    }

    rv = client.get('/api/v1/answers/1', headers=admin_logged_in_headers)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'Administrators are not authorized to proceed with this action',
        'status': 403
    }


def test_get_answer_not_found(client, logged_in_headers):
    """Test getting a non-existent answer using the answers/<id> route."""
    rv = client.get('/api/v1/answers/1', headers=logged_in_headers)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'The answer was not found',
        'status': 404
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
        'status': 401
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
            'question_id': 1,
            'url': 'http://localhost/api/v1/answers/1',
            'user_id': 1
        },
        {
            'id': 2,
            'question_id': 2,
            'url': 'http://localhost/api/v1/answers/2',
            'user_id': 1
        },
        {
            'id': 3,
            'question_id': 3,
            'url': 'http://localhost/api/v1/answers/3',
            'user_id': 1
        }
    ]
    assert json.loads(rv.data.decode('utf-8'))['items'] == items

    rv = client.get('/api/v1/answers', headers=admin_logged_in_headers)
    assert json.loads(rv.data.decode('utf-8')) == {
        'message': 'Administrators are not authorized to proceed with this action',
        'status': 403
    }
