import os
import tempfile

import pytest
from incontext import create_app
from incontext.db import get_db, init_db

with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
    _data_sql = f.read().decode('utf8')

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp() # creates and opens a temporary file 

    app = create_app({
        'TESTING': True, # tells Flask that the app is in test mode. makes testing better in Flask, and also tapped by extensions.
        'DATABASE': db_path, # override so it points to the temp path instead of the instance folder. 
    })

    with app.app_context(): # create the test db (at the temp file path)
        init_db()
        get_db().executescript(_data_sql)

    yield app

    os.close(db_fd) # test is over. close and remove the temp file.
    os.unlink(db_path)

@pytest.fixture
def client(app): # that's the application object created by the app fixture.
    return app.test_client() # this creates a test client for the app which will make requests to the app without running the server.

@pytest.fixture
def runner(app):
    return app.test_cli_runner() # so that the Click commands can be called.

# Pytest uses fixtures by matching their function names with the names of arguments in the test functions.

class AuthActions: # provide login and logout abstraction for certain tests
    def __init__(self, client):
        self._client = client

    def login(self, username='test', password='test'):
        return self._client.post(
            '/auth/login',
            data={'username': username, 'password': password}
        )

    def logout(self):
        return self._client.get('/auth/logout')


@pytest.fixture
def auth(client):
    return AuthActions(client)

