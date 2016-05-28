class TestUserFunctions:

    def test_user_login(self, loggedin_client):
        rv = loggedin_client.get('/', follow_redirects=True)
        assert 'Logout' in rv.data

    def test_config_page(self, loggedin_client):
        rv = loggedin_client.get('/configs', follow_redirects=True)
        assert 'ADReset2 Configuration' in rv.data

    def test_ad_config_page(self, loggedin_client):
        rv = loggedin_client.get('/ad_config', follow_redirects=True)
        assert 'Active Directory Connection Settings' in rv.data
