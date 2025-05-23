import pytest


def test_index(client, auth):
    response = client.get('/', follow_redirects=True) # when not logged in each page shows links to log in or register. 
    assert response.status_code == 200
    assert b'Log In' in response.data
    assert b'Register' in response.data

    auth.login()
    response = client.get('/') # the index view should display.
    assert b'href="/conversations/"' in response.data
