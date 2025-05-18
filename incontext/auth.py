import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from incontext.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth') # creates a blueprint named `'auth'`. It's passed `__name__` to know where it's defined. The `url_prefix` will be prepended to all URLs associated with the bp.

@bp.route('/register', methods=('GET', 'POST')) # associates the url `/register` with the `register` view function. So the function `register` will be called when Flask receives a request to `/auth/register`.
def register():
    if request.method == 'POST':
        username = request.form['username'] # request.form is a special type of dict mapping submitted form keys and values.
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    'INSERT INTO users (username, password) VALUES (?, ?)', (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError: # this will occur if the username already exists. (username column has a uniqueness constraint.)
                error = f'User {username} is already registered.'
            else:
                return redirect(url_for('auth.login')) # `url_for` generates the URL for the login view based on its name. this allows you to change the URL later without changing other code that links to it.

        flash(error) # `flash()` stores messages that can be retrieved when rendering the template.
    
    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
            ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password): # hashes the submitted password and and securely compares it with the stored password.
            error = 'Incorrect password.'

        if error is None:
            session.clear() # session is a dict that stores data across requests. 
            session['user_id'] = user['id'] # the user's id is stored in a new session. The data is stored in a cookie that is sent to the browser, and the browser then sends it back with subsequent requests. Flask securely signs the data so that it can't be tampered with.
            return redirect(url_for('index')) # now that the user's id is stored in session, it'll be available on subsequent requests. at the beginning of each request, if a user is logged in their info should be loaded and made available to other views.

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request # registers a function that runs before the view function no matter what URL was requested.
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone() # g.user lasts for the lasts for the length of the request.

@bp.route('/logout')
def logout():
    session.clear() # then load_logged_in_user won't load a user on subsequent requests.
    return redirect(url_for('index'))

def login_required(view): # decorator to check that a user is logged in. apply it to views that require authentication.
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


