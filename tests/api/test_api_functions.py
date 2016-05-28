import json
from mock import patch
from adreset2.models import AdConfigs
from adreset2.utils import ADException


class TestApiFunctions:

    def test_ad_configs_get(self, loggedin_client):
        rv = loggedin_client.get('/api/v1/ad_config', follow_redirects=True)
        try:
            json_rv = json.loads(rv.data)
        except:
            assert False, 'Not json'
        assert rv.status_code == 200
        assert json_rv['items'][0]['setting'] == 'domain_controller' and json_rv['items'][0]['value'] == 'example.local'
        assert json_rv['items'][1]['setting'] == 'port' and json_rv['items'][1]['value'] == '636'
        assert json_rv['items'][2]['setting'] == 'domain' and json_rv['items'][2]['value'] == 'example.local'
        assert json_rv['items'][3]['setting'] == 'username' and \
            json_rv['items'][3]['value'] == 'CN=svcADReset,CN=Users,DC=example,DC=local'
        assert json_rv['items'][4]['setting'] == 'password' and 'value' not in json_rv['items'][4]
        assert 'meta' in json_rv

    # Patch the try_ad_connection function so that Mocking LDAP isn't required here
    @patch('adreset2.utils.try_ad_connection', return_value=True)
    def test_ad_configs_post_replace(self, mocked_try_ad_connection, loggedin_client):
        rv = loggedin_client.post('/api/v1/ad_config', data=json.dumps(
            {'domain_controller': 'example.local', 'port': '636', 'domain': 'example.local',
             'username': 'CN=svcADReset,CN=Users,DC=example,DC=local', 'password': 'P@ssW0rd'}))
        try:
            json.loads(rv.data)
        except:
            assert False, 'Not json'
        assert rv.status_code == 201

    # Patch the try_ad_connection function so that Mocking LDAP isn't required here
    @patch('adreset2.utils.try_ad_connection', return_value=True)
    def test_ad_configs_post_new(self, mocked_try_ad_connection, loggedin_client):

        AdConfigs.query.delete()
        rv = loggedin_client.post('/api/v1/ad_config', data=json.dumps(
            {'domain_controller': 'example.local', 'port': '636', 'domain': 'example.local',
             'username': 'CN=svcADReset,CN=Users,DC=example,DC=local', 'password': 'P@ssW0rd'}))
        try:
            json.loads(rv.data)
        except:
            assert False, 'Not json'
        assert rv.status_code == 201

    # Patch the try_ad_connection function so that Mocking LDAP isn't required here
    @patch('adreset2.utils.try_ad_connection')
    def test_ad_configs_post_connection_fail(self, mocked_try_ad_connection, loggedin_client):
        mocked_try_ad_connection.side_effect = ADException('The username or password was incorrect')
        rv = loggedin_client.post('/api/v1/ad_config', data=json.dumps(
            {'domain_controller': 'example.local', 'port': '636', 'domain': 'example.local',
             'username': 'CN=svcADReset,CN=Users,DC=example,DC=local', 'password': 'P@ssW0rd'}))
        try:
            rv_json = json.loads(rv.data)
        except:
            assert False, 'Not json'
        assert rv.status_code == 400
        assert rv_json['message'] == 'The username or password was incorrect'

    def test_configs_get_one(self, loggedin_client):
        rv = loggedin_client.get('/api/v1/configs/1', follow_redirects=True)
        try:
            json.loads(rv.data)
        except:
            assert False, "Not json"
        assert rv.status_code == 200

    def test_configs_get_all(self, loggedin_client):
        rv = loggedin_client.get('/api/v1/configs', follow_redirects=True)
        try:
            json.loads(rv.data)
        except:
            assert False, "Not json"
        assert rv.status_code == 200

    def test_configs_update_pass(self, loggedin_client):
        rv = loggedin_client.put('/api/v1/configs/1', data=json.dumps(
            {'value': '5'}))
        assert rv.status_code == 200

    def test_configs_update_fail(self, loggedin_client):
        rv = loggedin_client.put('/api/v1/configs/1', data=json.dumps(
            {'someparameter': 'somevalue'}))
        assert rv.status_code == 400
        assert 'An invalid setting value was supplied' in rv.data

    def test_configs_update_log_file_fail(self, loggedin_client):
        """ Tests the update_config function (PUT route for configs) when a new log file
        path is specified but isn't writeable. A return value of an error is expected.
        """
        rv = loggedin_client.put("/api/v1/configs/4", data=json.dumps(
            {"value": "s0m3NonExistentDir/new_logfile.txt"}))
        assert rv.status_code == 400
        assert 'The specified log path is not writable' in rv.data
