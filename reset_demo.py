"""Explicitly recreate the local SQLite demonstration account and canonical tree.

Run: .venv/bin/python reset_demo.py
This utility refuses non-SQLite databases and asks before deleting only the demo
account's records. It is never imported by the application.
"""
from app import create_app, db
from app.models import User
from app.services.universe_service import create_root_universe, create_branch
from werkzeug.security import generate_password_hash


def main():
    app = create_app()
    if not app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:'):
        raise SystemExit('Refusing to run: reset_demo.py only supports SQLite.')
    if input('Reset only the local demo account and its realities? [y/N] ').strip().lower() != 'y':
        raise SystemExit('Cancelled.')
    with app.app_context():
        user = User.query.filter_by(username='demo').first()
        if user:
            # Relationships cascade events/decisions; remove child universes first.
            roots = user.universes.filter_by(parent_id=None).all()
            for root in roots:
                stack = [root]
                ordered = []
                while stack:
                    node = stack.pop(); ordered.append(node); stack.extend(node.children.all())
                for node in reversed(ordered): db.session.delete(node)
            db.session.delete(user); db.session.commit()
        user = User(username='demo', password_hash=generate_password_hash('demo123'))
        db.session.add(user); db.session.commit()
        root = create_root_universe(user, 'START', 'The origin of the demo multiverse.')
        study = create_branch(root, 'study', user)
        create_branch(study, 'work', user); create_branch(study, 'sleep', user)
        outing = create_branch(root, 'go_out', user)
        create_branch(outing, 'play_game', user)
        print('Demo ready: demo / demo123')


if __name__ == '__main__':
    main()
