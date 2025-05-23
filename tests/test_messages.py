import pytest
from incontext.db import get_db


def test_index(client, auth):
    response = client.get('/conversations/', follow_redirects=True) # when not logged in each page shows links to log in or register.
    # Note: The follow_redirects is new in just-conversations. Now login is indeed required for the entity (conversations) index page. The login_required decorator is commented out in just-contexts and just-agents, but if future it shouldn't be in a combined app.
    assert b'Log In' in response.data
    assert b'Register' in response.data

    auth.login()
    response = client.get('/conversations/') # the index view should display information about the conversation that was added with the test data.
    assert b'Log Out' in response.data # when logged in there's a ling to log out.
    assert b'test name' in response.data
    assert b'Created: 01.01.2025' in response.data
    assert b'Creator: test' in response.data
    assert b'href="/conversations/1/update"' in response.data


@pytest.mark.parametrize('path', (
    'conversations/create',
    'conversations/1/update',
    'conversations/1/delete',
))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers['Location'] == '/auth/login'


def test_creator_required(app, client, auth):
    # change the conversation creator to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE conversations SET creator_id = 3 WHERE id = 1')
        db.commit()

    auth.login()
    # current user can't modify another user's context
    assert client.post('conversations/1/update').status_code == 403
    assert client.post('conversations/1/delete').status_code == 403
    # current user doesn't see Edit link
    assert b'href="/conversations/1/update"' not in client.get('/conversations').data


@pytest.mark.parametrize('path', (
    'conversations/2/update',
    'conversations/2/delete',
))
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    auth.login()
    assert client.get('conversations/create').status_code == 200

    response = client.post('conversations/create', data={'name': 'created'})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM conversations').fetchone()[0]
        assert count == 2
    

def test_update(client, auth, app):
    auth.login()
    assert client.get('conversations/1/update').status_code == 200
    
    client.post('/conversations/1/update', data={'name': 'updated'})

    with app.app_context():
        db = get_db()
        conversation = db.execute('SELECT * FROM conversations WHERE id = 1').fetchone()
        assert conversation['name'] == 'updated'


@pytest.mark.parametrize('path', (
    '/conversations/create',
    '/conversations/1/update',
))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={'name': ''})
    assert b'Name is required.' in response.data


def test_view(client, auth):
    response = client.get('/conversations/1', follow_redirects=True) # when not logged in each page shows links to log in or register.
    # Note: The follow_redirects is new in just-conversations. Now login is indeed required for the entity (conversations) index page. The login_required decorator is commented out in just-contexts and just-agents, but if future it shouldn't be in a combined app.
    assert b'Log In' in response.data
    assert b'Register' in response.data

    auth.login()
    response = client.get('/conversations/1')
    assert b'Log Out' in response.data
    assert b'Conversation "test name"' in response.data


def test_delete(client, auth, app): # the delete view should should redirect to the index url and the conversation should no longer exist in the db.
    auth.login()
    response = client.post('/conversations/1/delete')
    assert response.headers['Location'] == '/conversations/'

    with app.app_context():
        db = get_db()
        conversation = db.execute('SELECT * FROM conversations WHERE id = 1').fetchone()
        assert conversation is None
