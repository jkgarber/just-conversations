from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required
from incontext.db import get_db
from openai import OpenAI
import os

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
    return render_template('conversations/view.html', conversation=conversation, messages=messages)


def get_messages(conversation_id):
    messages = get_db().execute(
        'SELECT m.id, m.content, m.human, m.created, c.creator_id'
        ' FROM messages m'
        ' JOIN conversations c'
        ' ON m.conversation_id = c.id'
        ' WHERE c.id = ?',
        (conversation_id,)
    ).fetchall()
    
    return messages


def delete_messages(conversation_id):
    db = get_db()
    db.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
    db.commit()


def get_credential(name):
    os_env_var = os.environ.get(name)
    if os_env_var is not None:
        return os_env_var
    else:
        credential_path = os.environ.get('CREDENTIALS_DIRECTORY')
        with open(f'{credential_path}/{name}') as f:
            credential = f.read().strip()
            return credential


def get_agent_response(cid):
    messages = get_messages(cid)
    conversation_history = [dict(role='system', content='You are a helpful assistant.')]
    for message in messages:
        human = message['human']
        role = 'user' if human == 1 else 'assistant'
        content = message['content']
        conversation_history.append(dict(role=role, content=content))
    
    openai_api_key = get_credential('OPENAI_API_KEY')
    client = OpenAI(api_key=openai_api_key)
    try:
        response = client.responses.create(
            model='gpt-4.1-mini',
            input=conversation_history
        )
        return dict(success=True, content=response.output_text)
    except Exception as e:
        return dict(success=False, content=e)
    

@bp.route('/<int:conversation_id>/add-message', methods=('POST',))
@login_required
def add_message(conversation_id):
    conversation = get_conversation(conversation_id) # To check the creator
    message_content = request.json['content']
    error = None

    if not message_content:
        error = 'Message can\'t be empty.'

    if error is not None:
        return error, 400
    else:
        db = get_db()
        db.execute(
            'INSERT INTO messages (conversation_id, content, human)'
            ' VALUES (?, ?, ?)',
            (conversation_id, message_content, 1,)
        )
        db.commit()
        return '', 200


@bp.route('/<int:conversation_id>/agent-response', methods=('POST',))
@login_required
def agent_response(conversation_id):
    conversation = get_conversation(conversation_id) # To check the creator
    agent_response = get_agent_response(conversation_id)
    if agent_response['success']:
        db = get_db()
        db.execute(
            'INSERT INTO messages (conversation_id, content, human)'
            'VALUES (?, ?, ?)',
            (conversation_id, agent_response['content'], 0,)
        )
        db.commit()
        return {'content': agent_response['content']}, 200
    else:
        # print(agent_response['content']) # Log the error
        return 'The Agent\'s API returned an error.', 200
