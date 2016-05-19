import pytest
from adreset2 import app, db
from adreset2.utils import add_default_configuration_settings
from adreset2.models import AdConfigs

app.config.from_object('config.TestConfiguration')
SQLALCHEMY_DATABASE_URI = app.config['SQLALCHEMY_DATABASE_URI']


def initialize():
    try:
        db.session.remove()
        db.drop_all()
        db.create_all()
        add_default_configuration_settings()
        db.session.add(AdConfigs().from_key_pair('domain_controller', 'example.local'))
        db.session.add(AdConfigs().from_key_pair('port', '636'))
        db.session.add(AdConfigs().from_key_pair('domain', 'example.local'))
        db.session.add(AdConfigs().from_key_pair('username', 'CN=svcADReset,CN=Users,DC=example,DC=local'))
        db.session.add(AdConfigs().from_key_pair('password', 'P@ssW0rd'))
        db.session.commit()
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
