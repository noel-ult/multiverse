"""Development-only seed script for the sibling-branching test tree.

Creates (for the dedicated user dev/dev123):

    START
    |-- STUDY
    |   |-- WORK
    |   `-- SLEEP
    `-- GO OUT
        `-- PLAY GAME

This is for TESTING the multiverse / sibling-branching UX only.
It never deletes data and never touches other users. If the dev user
already has a root reality from a previous run, the script exits early.
"""

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import User, Universe
from app.services.universe_service import create_root_universe, create_branch


def seed_dev():
    app = create_app()
    with app.app_context():
        dev = User.query.filter_by(username='dev').first()
        if not dev:
            dev = User(
                username='dev',
                password_hash=generate_password_hash('dev123'),
            )
            db.session.add(dev)
            db.session.flush()
            print('Created dev user: dev / dev123')
        else:
            print('Reusing existing dev user: dev / dev123')

        if Universe.query.filter_by(user_id=dev.id, parent_id=None).first():
            print('Dev tree already exists for user "dev". Nothing to do.')
            return

        start = create_root_universe(dev)

        study = create_branch(start, 'study', dev)
        create_branch(study, 'work', dev)
        create_branch(study, 'sleep', dev)

        go_out = create_branch(start, 'go_out', dev)
        create_branch(go_out, 'play_game', dev)

        print('Dev sibling tree created:')
        print('  START') 
        print('  |-- STUDY')
        print('  |   |-- WORK')
        print('  |   `-- SLEEP')
        print('  `-- GO OUT')
        print('      `-- PLAY GAME')


if __name__ == '__main__':
    seed_dev()