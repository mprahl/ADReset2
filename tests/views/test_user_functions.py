from adreset2 import app

class TestViews:

    def test_index(self, loggedin_client):
        rv = loggedin_client.get("/", follow_redirects=True)
        assert "Hello World" in rv.data
