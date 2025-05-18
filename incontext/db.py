import os
import sqlite3
from datetime import datetime

import click
from flask import current_app, g


def get_db():
    if 'db' not in g: # `g` is the application context global - a special object unique for each request. It is used for data that might be accessed by multiple functions during the request. This conditional ensures that for any given request there is only one connection to the database.
        g.db = sqlite3.connect( # establishes a connection to the file pointed at by the `DATABASE` configuration key. This file doesn't have to exist yet, and won't until the database is initialized. (see protocol doc).
            current_app.config['DATABASE'], # `current_app` is also a special object. It points to the Flask application handling the request. It's available because the project uses an application factory in `__init__.py`. `get_db` will be called while the application is handling a request. It's not being called outside of that context. Therefore `current_app` will be available.
            detect_types=sqlite3.PARSE_DECLTYPES # Does things like parsing timestamps to python datetime objects because sqlite has only very few native data types (INTEGER, TEXT, REAL, and BLOB).
        )
        g.db.row_factory = sqlite3.Row # returns rows that behave like dicts, allowing access to the columns by name.

    return g.db


def close_db(e=None):
    '''Checks if a connection was created and closes it if so. Called by the application factory after each request.'''
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db() # returns a database connection

    with current_app.open_resource('schema.sql') as f: # `open_resource` opens a file relative to the `incontext` package
        db.executescript(f.read().decode('utf-8'))
  
    db.execute('INSERT INTO users (username, password) VALUES(?, ?)',('admin', os.environ.get('IC_ADMIN_PW')),)
    db.commit()


@click.command('init-db') # defines a command line command 
def init_db_command():
    '''Clear the existing data and create new tables.'''
    init_db()
    click.echo('Initialized the database.')


# tell python how to interpret timestamp values in the database
sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)


def init_app(app):
    '''Called by the app factory to do these register actions on the app.'''
    app.teardown_appcontext(close_db) # register the `close_db` function with the process of cleaning up after returning the response
    app.cli.add_command(init_db_command) # registers the `init-db` command that can be called with the `flask` command
