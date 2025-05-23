from incontext import create_app

# there's not much to test in the factory, just the passing of test config for now.
def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing
