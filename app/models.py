from datetime import datetime, timezone

from sqlalchemy import Index, event

from app import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    universes = db.relationship('Universe', back_populates='user', lazy='dynamic')

    __table_args__ = (
        Index('ix_users_username', 'username'),
    )

    def __repr__(self):
        return f'<User {self.username}>'


class Universe(db.Model):
    __tablename__ = 'universes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('universes.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    state_json = db.Column(db.Text, nullable=False, default='{}')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', back_populates='universes')
    parent = db.relationship('Universe', remote_side='Universe.id', back_populates='children')
    children = db.relationship('Universe', back_populates='parent', lazy='dynamic')
    decisions = db.relationship('Decision', back_populates='universe', lazy='dynamic',
                                cascade='all, delete-orphan')
    events = db.relationship('Event', back_populates='universe', lazy='dynamic',
                             cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_universes_user_id', 'user_id'),
        Index('ix_universes_parent_id', 'parent_id'),
    )

    def get_state(self):
        import json
        try:
            return json.loads(self.state_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_state(self, state):
        import json
        self.state_json = json.dumps(state)

    def __repr__(self):
        return f'<Universe {self.name}>'


class Decision(db.Model):
    __tablename__ = 'decisions'

    id = db.Column(db.Integer, primary_key=True)
    universe_id = db.Column(db.Integer, db.ForeignKey('universes.id'), nullable=False)
    choice = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    universe = db.relationship('Universe', back_populates='decisions')

    __table_args__ = (
        Index('ix_decisions_universe_id', 'universe_id'),
    )

    def __repr__(self):
        return f'<Decision {self.choice}>'


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    universe_id = db.Column(db.Integer, db.ForeignKey('universes.id'), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    meta_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    universe = db.relationship('Universe', back_populates='events')

    __table_args__ = (
        Index('ix_events_universe_id', 'universe_id'),
    )

    def __repr__(self):
        return f'<Event {self.event_type}>'


@event.listens_for(User.username, 'set')
def validate_username(target, value, oldvalue, initiator):
    if not value or not value.strip():
        raise ValueError('username cannot be empty')


@event.listens_for(Universe.name, 'set')
def validate_universe_name(target, value, oldvalue, initiator):
    if not value or not value.strip():
        raise ValueError('universe name cannot be empty')


@event.listens_for(Decision.choice, 'set')
def validate_decision_choice(target, value, oldvalue, initiator):
    if not value or not value.strip():
        raise ValueError('decision choice cannot be empty')


@event.listens_for(Event.description, 'set')
def validate_event_description(target, value, oldvalue, initiator):
    if not value or not value.strip():
        raise ValueError('event description cannot be empty')
