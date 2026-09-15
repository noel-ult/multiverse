import json

from app import db
from app.models import Universe, Decision, Event
from app.services.consequence_service import (
    evaluate_consequence,
    evaluate_milestones,
    calculate_reality_score,
)

INITIAL_STATE = {
    'money': 1000,
    'energy': 100,
    'knowledge': 50,
    'career': 0,
    'relationships': 50,
}

DECISIONS = {
    'study': {
        'label': 'Study',
        'description': 'Spend time improving your knowledge.',
        'effects': {'energy': -15, 'knowledge': 15, 'career': 5},
        'consequence': 'You spent the evening mastering a difficult topic.',
    },
    'work': {
        'label': 'Work',
        'description': 'Spend the day working.',
        'effects': {'money': 300, 'energy': -20, 'career': 10},
        'consequence': 'Your hard work improved both your finances and career.',
    },
    'sleep': {
        'label': 'Sleep',
        'description': 'Rest and recover.',
        'effects': {'energy': 25},
        'consequence': 'You chose rest over productivity and recovered your energy.',
    },
    'go_out': {
        'label': 'Go Out',
        'description': 'Spend time outside.',
        'effects': {'energy': -10, 'relationships': 10, 'money': -100},
        'consequence': 'You spent the evening socializing and met new people.',
    },
    'play_game': {
        'label': 'Play Game',
        'description': 'Relax and have fun.',
        'effects': {'energy': -5, 'relationships': 5},
        'consequence': 'A relaxing night helped you unwind.',
    },
    'learn': {
        'label': 'Learn Something New',
        'description': 'Develop a new skill.',
        'effects': {'energy': -10, 'knowledge': 20},
        'consequence': 'You discovered an unexpected interest.',
    },
    'meet_friend': {
        'label': 'Meet a Friend',
        'description': 'Spend meaningful time with a friend.',
        'effects': {'energy': -10, 'relationships': 15},
        'consequence': 'A conversation gave you a new perspective.',
    },
    'advanced_challenge': {
        'label': 'Advanced Challenge',
        'description': 'Push yourself with a complex problem.',
        'effects': {'energy': -20, 'knowledge': 20, 'career': 10},
        'consequence': 'You took on a challenge beyond your usual comfort zone.',
        'prerequisites': {'knowledge': 70},
        'unlock_reason': 'Requires Knowledge 70',
    },
    'promotion': {
        'label': 'Apply for Promotion',
        'description': 'Ask for a higher position.',
        'effects': {'money': 500, 'energy': -25, 'career': 15},
        'consequence': 'You negotiated a promotion based on your career progress.',
        'prerequisites': {'career': 40},
        'unlock_reason': 'Requires Career 40',
    },
    'side_project': {
        'label': 'Start a Side Project',
        'description': 'Invest savings into a side project.',
        'effects': {'money': -500, 'energy': -20, 'knowledge': 10, 'career': 15},
        'consequence': 'You used your savings to fund a promising side project.',
        'prerequisites': {'money': 1500},
        'unlock_reason': 'Requires Money 1500',
    },
}

_STAT_LABELS = {
    'knowledge': 'Knowledge',
    'career': 'Career',
    'relationships': 'Relationships',
    'energy': 'Energy',
    'money': 'Money',
}


def apply_effects(state, effects):
    new_state = dict(state)
    for key, delta in effects.items():
        new_state[key] = new_state.get(key, 0) + delta
        if key == 'money':
            new_state[key] = max(0, new_state[key])
        else:
            new_state[key] = max(0, min(100, new_state[key]))
    return new_state


def decision_is_available(decision_key, state):
    """Return (available, reason). Validates prerequisites against a state."""
    cfg = DECISIONS.get(decision_key)
    if not cfg:
        return False, 'Unknown decision.'
    prereqs = cfg.get('prerequisites')
    if not prereqs:
        return True, None
    missing = [_STAT_LABELS.get(k, k) + ' ' + str(v)
               for k, v in prereqs.items() if state.get(k, 0) < v]
    if missing:
        return False, 'Requires ' + ', '.join(missing)
    return True, None


def get_available_decisions(universe):
    """Return normal + special decisions, each tagged with unlock state."""
    state = universe.get_state()
    available = []
    for key, cfg in DECISIONS.items():
        if cfg.get('prerequisites'):
            available_state, reason = decision_is_available(key, state)
            available.append({
                'key': key,
                'label': cfg['label'],
                'description': cfg['description'],
                'effects': cfg['effects'],
                'consequence': cfg.get('consequence', ''),
                'unlocked': available_state,
                'unlock_reason': reason if not available_state else None,
            })
        else:
            available.append({
                'key': key,
                'label': cfg['label'],
                'description': cfg['description'],
                'effects': cfg['effects'],
                'consequence': cfg.get('consequence', ''),
                'unlocked': True,
                'unlock_reason': None,
            })
    return available


def create_root_universe(user, name='START', description='The beginning of all possibilities.'):
    universe = Universe(
        user_id=user.id,
        parent_id=None,
        name=name,
        description=description,
    )
    universe.set_state(INITIAL_STATE)
    db.session.add(universe)
    db.session.flush()

    event = Event(
        universe_id=universe.id,
        event_type='creation',
        description='Universe created.',
        meta_json=json.dumps({'initial_state': INITIAL_STATE}),
    )
    db.session.add(event)
    db.session.commit()
    return universe


def create_branch(parent_universe, decision_key, user):
    if parent_universe.user_id != user.id:
        raise PermissionError('Access denied.')

    if decision_key not in DECISIONS:
        raise ValueError(f'Unknown decision: {decision_key}')

    decision_cfg = DECISIONS[decision_key]
    parent_state = parent_universe.get_state()

    available, reason = decision_is_available(decision_key, parent_state)
    if not available:
        raise ValueError(reason)

    new_state = apply_effects(parent_state, decision_cfg['effects'])

    new_name = f'{parent_universe.name} — {decision_cfg["label"]}'
    if len(new_name) > 100:
        new_name = new_name[:100]

    new_description = decision_cfg.get('consequence') or decision_cfg['description']

    try:
        child = Universe(
            user_id=parent_universe.user_id,
            parent_id=parent_universe.id,
            name=new_name,
            description=new_description,
        )
        child.set_state(new_state)
        db.session.add(child)
        db.session.flush()

        decision = Decision(
            universe_id=child.id,
            choice=decision_cfg['label'],
        )
        db.session.add(decision)

        event = Event(
            universe_id=child.id,
            event_type='decision',
            description=f'Chose to {decision_cfg["label"].lower()}.',
            meta_json=json.dumps({
                'decision': decision_key,
                'effects': decision_cfg['effects'],
            }),
        )
        db.session.add(event)

        consequence = evaluate_consequence(decision_key, parent_state, new_state)
        con_event = Event(
            universe_id=child.id,
            event_type='consequence',
            description=consequence['description'],
            meta_json=json.dumps({
                'decision': decision_key,
                'effects': decision_cfg['effects'],
                'consequence_type': consequence['type'],
                'title': consequence['title'],
            }),
        )
        db.session.add(con_event)

        for milestone in evaluate_milestones(parent_state, new_state):
            ms_event = Event(
                universe_id=child.id,
                event_type='milestone',
                description=milestone['description'],
                meta_json=json.dumps({
                    'type': milestone['type'],
                    'threshold': milestone['threshold'],
                    'title': milestone['title'],
                }),
            )
            db.session.add(ms_event)

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return child


def get_universe_tree(universe):
    state = universe.get_state()
    events = Event.query.filter_by(universe_id=universe.id).all()
    milestones = sum(1 for e in events if e.event_type == 'milestone')
    return {
        'id': universe.id,
        'name': universe.name,
        'parent_id': universe.parent_id,
        'score': calculate_reality_score(state),
        'energy': state.get('energy', 0),
        'milestones': milestones,
        'state': state,
        'created_from': universe.decisions.first().choice if universe.parent_id and universe.decisions.first() else None,
        'children': [get_universe_tree(c) for c in universe.children],
    }


def get_root_universe(universe):
    current = universe
    visited = set()
    while current.parent_id is not None:
        if current.id in visited:
            raise ValueError('Circular reference detected.')
        visited.add(current.id)
        current = db.session.get(Universe, current.parent_id)
        if current is None:
            raise ValueError('Broken parent reference.')
    return current


def get_universe_timeline(universe):
    chain = []
    current = universe
    visited = set()
    while current is not None:
        if current.id in visited:
            raise ValueError('Circular reference detected.')
        visited.add(current.id)
        chain.append(current)
        current = db.session.get(Universe, current.parent_id) if current.parent_id else None
    chain.reverse()

    timeline = []
    for u in chain:
        events = Event.query.filter_by(universe_id=u.id).order_by(Event.created_at).all()
        timeline.append({
            'universe_id': u.id,
            'name': u.name,
            'events': [{
                'id': e.id,
                'type': e.event_type,
                'description': e.description,
                'metadata': json.loads(e.meta_json) if e.meta_json else None,
            } for e in events],
        })
    return timeline
