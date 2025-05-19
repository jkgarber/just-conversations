from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required
from incontext.db import get_db
from incontext.messages import get_messages, delete_messages

bp = Blueprint('conversations', __name__, url_prefix='/conversations')

@bp.route('/')
@login_required
def index():
    db = get_db()
    conversations = db.execute(
        'SELECT c.id, name, created, creator_id, username'
        ' FROM conversations c JOIN users u ON c.creator_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('conversations/index.html', conversations=conversations)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        error = None

        if not name:
            error = 'Name is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO conversations (name, creator_id)'
                ' VALUES (?, ?)',
                (name, g.user['id'])
            )
            db.commit()
            return redirect(url_for('conversations.index'))

    return render_template('conversations/create.html')

def get_conversation(id, check_creator=True):
    conversation = get_db().execute(
        'SELECT c.id, name, created, creator_id, username'
        ' FROM conversations c JOIN users u ON c.creator_id = u.id'
        ' WHERE c.id = ?',
        (id,)
    ).fetchone()

    if conversation is None:
        abort(404, f"Conversation id {id} doesn't exist.")

    if check_creator and conversation['creator_id'] != g.user['id']:
        abort(403) # 403 means Forbidden. 401 means "Unauthorized" but you redirect to the login page instead of returning that status.

    return conversation

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    conversation = get_conversation(id)

    if request.method == 'POST':
        name = request.form['name']
        error = None

        if not name:
            error = 'Name is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE conversations SET name = ?'
                ' WHERE id = ?',
                (name, id)
            )
            db.commit()
            return redirect(url_for('conversations.index'))
    
    return render_template('conversations/update.html', conversation=conversation)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_conversation(id)
    db = get_db()
    db.execute('DELETE FROM conversations WHERE id = ?', (id,))
    db.commit()
    delete_messages(id)
    return redirect(url_for('conversations.index'))

@bp.route('/<int:id>', methods=('GET',))
@login_required
def view(id):
    conversation = get_conversation(id)
    messages = get_messages(id)
    forms = ['1']
    return render_template('conversations/view.html', conversation=conversation, messages=messages, forms=forms)

