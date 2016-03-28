import pytest
from adreset2 import app, db

app.config.from_object('config.TestConfiguration')
SQLALCHEMY_DATABASE_URI = app.config['SQLALCHEMY_DATABASE_URI']

def initialize():
    try:
        db.session.remove()
        db.drop_all()
        db.create_all()
        return True

    except Exception as e:
        print "Unexpected error: {0}".format(e.message)

    return False

# Create a fresh database
initialize()


@pytest.fixture(scope='module')
def loggedin_client():
    client = app.test_client()

    return client
