import secrets
from functools import wraps

from flask import session, redirect, request, abort, url_for

from app import db
from app.models import User, Universe


def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            next_path = request.path
            return redirect(url_for('auth.login', next=next_path))
        return f(user=user, *args, **kwargs)
    return decorated


def get_owned_universe(universe_id, user):
    universe = db.session.get(Universe, universe_id)
    if not universe:
        abort(404)
    if universe.user_id != user.id:
        abort(403)
    return universe


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def validate_csrf_token():
    token = session.get('_csrf_token')
    form_token = request.form.get('_csrf_token')
    if not token or not form_token or not secrets.compare_digest(token, form_token):
        abort(403)
