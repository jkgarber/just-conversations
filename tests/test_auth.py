import pytest
from flask import g, session
from incontext.db import get_db

def test_register(client, app):
    assert client.get('/auth/register').status_code == 200 # the register view should render successfully on GET
    response = client.post( # `client.post` converts the `data` dict into form data.
        'auth/register', data={'username': 'a', 'password': 'a'}
    )
    assert response.headers["Location"] == "/auth/login" # the register view should redirect to the login URL on POST.

    with app.app_context():
        assert get_db().execute(
            "SELECT * FROM users WHERE username = 'a'",
        ).fetchone() is not None # the user's data should be in the database.

@pytest.mark.parametrize(('username', 'password', 'message'), ( # runs the same test function with different arguments.
    ('', '', b'Username is required.'),
    ('a', '', b'Password is required.'),
    ('test', 'test', b'already registered'),
))
def test_register_validate_input(client, username, password, message):
    response = client.post(
        'auth/register',
        data={'username': username, 'password': password}
    )
    assert message in response.data # `data` contains the body of the response as bytes. if you want to compare text, use get_data(as_text=True)

def test_login(client, auth):
    assert client.get('auth/login').status_code == 200
    response = auth.login()
    assert response.headers["Location"] == "/"

    with client: # using client in a with block allows accessing context variables such as session after the response is returned. 
        client.get('/')
        assert session['user_id'] == 2
        assert g.user['username'] == 'test'


@pytest.mark.parametrize(('username', 'password', 'message'), (
    ('a', 'test', b'Incorrect username'),
    ('test', 'b', b'Incorrect password'),
))
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password)
    assert message in response.data


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert 'user_id' not in session
