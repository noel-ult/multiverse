from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import User
from app.services.universe_service import create_root_universe, create_branch


def seed():
    app = create_app()
    with app.app_context():
        if User.query.filter_by(username='demo').first():
            print('Seed data already exists.')
            return

        demo = User(
            username='demo',
            password_hash=generate_password_hash('demo123'),
        )
        db.session.add(demo)
        db.session.flush()

        start = create_root_universe(demo)

        study = create_branch(start, 'study', demo)
        create_branch(study, 'work', demo)

        go_out = create_branch(start, 'go_out', demo)
        create_branch(go_out, 'play_game', demo)

        print('Seed data created.')
        print('  demo / demo123')


if __name__ == '__main__':
    seed()
