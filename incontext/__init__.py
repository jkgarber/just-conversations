import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

def create_app(test_config=None):
    '''This is the application factory function: configuration, registration, and other setup.'''
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True) # creates the flask instance. `__name__` is the name of the current python module (incontext). It will be used for setting up paths. `instance_relative_config=True` tells the app that config files are relative to the instance folder, which is located outside of the package.
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )
    app.config.from_mapping( # sets some default configuration.
        SECRET_KEY='dev', # used by Flask and extensions to keep data safe. should be overridden with a random valye when deploying.
        DATABASE=os.path.join(app.instance_path, 'incontext.sqlite'), # the path where the sqlite database will be saved. `app.instance_path` is the path that Flask has chosen for the instance folder.
    )
    
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True) # overrides the default config with values taken from the `config.py` file in the instance folder if it exists. For example, when deploying, this can be used to set a real `SECRET_KEY`.
    else:
        # load the test config if passed in
	    app.config.from_mapping(test_config) # `test_config` can also be passed to the factory, and will be used instead of the instance config. This is so the tests can be configured independently of any development config values.

    # ensure the instance folder exists
    try:
	    os.makedirs(app.instance_path) # Flask doesn't create the instance folder automatically, but it needs to be created because your project will create the sqlite database file there.
    except OSError:
	    pass

    from . import db
    db.init_app(app) # calling the function to register a couple of database-related things with the app
    
    from . import auth
    app.register_blueprint(auth.bp) # has views for login, register, and logout.

    from . import home
    app.register_blueprint(home.bp)
    app.add_url_rule('/', endpoint='index') # you can now use `url_for('index')` for `url_for('home.index')` because there is no url prefix for the home bp.

    from . import conversations
    app.register_blueprint(conversations.bp)

    from . import messages
    app.register_blueprint(messages.bp)
    
    return app
