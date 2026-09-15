from flask import Blueprint, render_template, request, redirect, flash, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models import User
from app.services.auth_service import generate_csrf_token, validate_csrf_token

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        validate_csrf_token()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        errors = []
        if not username:
            errors.append('Username is required.')
        elif len(username) > 100:
            errors.append('Username is too long.')
        elif User.query.filter_by(username=username).first():
            errors.append('Username already taken.')

        if not password:
            errors.append('Password is required.')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters.')

        if password != confirm:
            errors.append('Passwords do not match.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('register.html')

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        flash(f'Welcome, {username}!', 'success')
        return redirect(url_for('main.list_universes'))

    return render_template('register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        validate_csrf_token()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            next_url = request.args.get('next', '')
            if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                return redirect(next_url)
            return redirect(url_for('main.list_universes'))

        flash('Invalid username or password.', 'error')
        return render_template('login.html')

    return render_template('login.html')


@bp.route('/logout', methods=['POST'])
def logout():
    validate_csrf_token()
    session.clear()
    flash('LOGOUT SUCCESSFUL', 'info')
    return redirect(url_for('main.index'))
