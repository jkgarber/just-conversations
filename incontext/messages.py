from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required
from incontext.db import get_db

from openai import OpenAI

bp = Blueprint('messages', __name__, url_prefix='/messages')


def get_messages(conversation_id, check_creator=True):
    messages = get_db().execute(
        'SELECT m.id, m.content, m.human, m.created, c.creator_id'
        ' FROM messages m'
        ' JOIN conversations c'
        ' ON m.conversation_id = c.id'
        ' WHERE c.id = ?',
        (conversation_id,)
    ).fetchall()
    
    if len(messages) > 0 and check_creator and messages[0]['creator_id'] != g.user['id']:
        abort(403) # 403 means Forbidden. 401 means "Unauthorized" but you redirect to the login page instead of returning that status.

    return messages


def delete_messages(conversation_id):
    db = get_db()
    db.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
    db.commit()


@bp.route('/<int:conversation_id>', methods=('GET',))
@login_required
def conversation_messages(conversation_id):
    messages = get_messages(conversation_id)
    return messages


def get_agent_response(cid):
    messages = get_messages(cid)
    conversation_history = [dict(role='system', content='You are a helpful assistant.')]
    for message in messages:
        human = message['human']
        if human == 1:
            role = 'user'
        elif human == 0:
            role = 'assistant'
        content = message['content']
        conversation_history.append(dict(role=role, content=content))

    client = OpenAI()
    try:
        response = client.responses.create(
            model='gpt-4.1-mini',
            input=conversation_history
        )
        return dict(success=True, content=response.output_text)
    except Exception as e:
        return dict(success=False, content=f'Error: {str(e)}')
    

@bp.route('/<int:conversation_id>/add', methods=('POST',))
@login_required
def add_message(conversation_id):
    message_content = request.json['content']
    error = None

    if not message_content:
        error = 'Message can\'t be empty.'

    if error is not None:
        flash(error)
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
    elif not agent_response['success']:
        return 'The Agent\'s API returned an error.', 200
