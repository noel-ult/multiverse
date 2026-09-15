"""Standalone test suite for the Multiverse app (no pytest required).

Run:  .venv/bin/python tests/run_tests.py
Uses an isolated in-memory SQLite database so the real data is untouched.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Isolate the test run BEFORE importing the app: config.py reads DATABASE_URL
# from the environment at import time. Flask-SQLAlchemy caches the engine per
# app, so overriding app.config afterwards is NOT sufficient — that would send
# test writes to the real instance/multiverse.db.
_TMP_DIR = tempfile.mkdtemp(prefix='multiverse_test_')
_TMP_DB = os.path.join(_TMP_DIR, 'test.db')
os.environ['DATABASE_URL'] = 'sqlite:///' + _TMP_DB

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import User, Universe, Event
from app.services.universe_service import (
    DECISIONS,
    INITIAL_STATE,
    apply_effects,
    decision_is_available,
    get_available_decisions,
    create_root_universe,
    create_branch,
    get_universe_tree,
    get_universe_timeline,
)
from app.services.consequence_service import (
    calculate_reality_score,
    get_reality_status,
    evaluate_consequence,
    evaluate_milestones,
    get_reality_summary,
)

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, True, ''))
        print('PASS  ' + name)
    except AssertionError as e:
        RESULTS.append((name, False, str(e)))
        print('FAIL  ' + name + '  ->  ' + str(e))
    except Exception as e:
        RESULTS.append((name, False, 'EXC: ' + repr(e)))
        print('ERROR ' + name + '  ->  ' + repr(e))


def _new_app_with_tmp_db():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app, _TMP_DB


def _make_user(app, username):
    user = User(username=username,
                password_hash=generate_password_hash('pw123456'))
    db.session.add(user)
    db.session.commit()
    return user


def _login(client, app, user):
    """Log a user in through the real form flow and return a seeded CSRF token."""
    with client.session_transaction() as sess:
        sess['_csrf_token'] = 'testtoken'
    r = client.post('/login', data={
        'username': user.username,
        'password': 'pw123456',
        '_csrf_token': 'testtoken',
    })
    assert r.status_code == 302, r.status_code
    return app


def _make_root(app, user):
    return create_root_universe(user)


def _state_of(u):
    return u.get_state()


def _events_of(app, u):
    return Event.query.filter_by(universe_id=u.id).order_by(Event.created_at).all()


def _types_of(app, u):
    return [e.event_type for e in _events_of(app, u)]


# ------------------------------------------------------------------
# consequence_service
# ------------------------------------------------------------------

def test_score_formula():
    base = calculate_reality_score(INITIAL_STATE)
    # money 1000/30=33.3, energy 100, knowledge 50, career 0, relationships 50 -> avg 46.67
    assert base == 47, base
    perfect = calculate_reality_score({'money': 3000, 'energy': 100, 'knowledge': 100, 'career': 100, 'relationships': 100})
    assert perfect == 100, perfect
    empty = calculate_reality_score({})
    assert empty == 0, empty


def test_status_thresholds():
    assert get_reality_status(25) == 'Fragile Reality'
    assert get_reality_status(26) == 'Unstable Reality'
    assert get_reality_status(50) == 'Unstable Reality'
    assert get_reality_status(51) == 'Balanced Reality'
    assert get_reality_status(75) == 'Balanced Reality'
    assert get_reality_status(76) == 'Thriving Reality'
    assert get_reality_status(90) == 'Thriving Reality'
    assert get_reality_status(91) == 'Exceptional Reality'


def test_consequence_normal():
    old = dict(INITIAL_STATE)
    new = apply_effects(old, DECISIONS['study']['effects'])
    con = evaluate_consequence('study', old, new)
    assert con['type'] == 'effect', con
    assert con['title'] == 'Study'
    assert con['description'] == DECISIONS['study']['consequence']
    assert con['effects'] == DECISIONS['study']['effects']


def test_consequence_threshold_knowledge():
    old = dict(INITIAL_STATE); old['knowledge'] = 70
    new = dict(old); new['knowledge'] = 85   # crosses >= 80
    con = evaluate_consequence('study', old, new)
    assert con['type'] == 'opportunity', con
    assert con['title'] == 'New Opportunity'


def test_consequence_threshold_energy_low():
    old = dict(INITIAL_STATE); old['energy'] = 30
    new = dict(old); new['energy'] = 15     # crosses <= 20
    con = evaluate_consequence('work', old, new)
    assert con['type'] == 'running_low', con


def test_milestones_purity():
    old = dict(INITIAL_STATE); old['knowledge'] = 60
    new = dict(old); new['knowledge'] = 80
    out = evaluate_milestones(old, new)
    assert len(out) == 1 and out[0]['type'] == 'knowledge' and out[0]['threshold'] == 75
    # same crossing again yields the same single result (no drift / no duplicates in a run)
    out2 = evaluate_milestones(old, new)
    assert out2 == out


def test_milestones_no_recross():
    old = dict(INITIAL_STATE); old['knowledge'] = 75
    new = dict(old); new['knowledge'] = 70
    assert evaluate_milestones(old, new) == []


def test_reality_summary():
    a = {'knowledge': 90, 'career': 10, 'relationships': 50, 'energy': 50, 'money': 10}
    b = {'knowledge': 40, 'career': 60, 'relationships': 50, 'energy': 50, 'money': 10}
    s = get_reality_summary(a, b)
    assert 'Universe A is stronger in knowledge' in s
    assert 'Universe B is stronger in career' in s
    assert get_reality_summary(a, a) == 'Universe A and Universe B are identical in every field.'


# ------------------------------------------------------------------
# universe_service pure helpers
# ------------------------------------------------------------------

def test_apply_effects_clamps():
    s = dict(INITIAL_STATE)
    s['money'] = 10
    s['energy'] = 95
    s['knowledge'] = 90
    out = apply_effects(s, {'money': -500, 'energy': 30, 'knowledge': 30})
    assert out['money'] == 0           # floor
    assert out['energy'] == 100        # ceiling
    assert out['knowledge'] == 100     # ceiling


def test_decision_availability_gates():
    low_state = dict(INITIAL_STATE)
    assert decision_is_available('advanced_challenge', low_state)[0] is False
    high_knowledge = dict(INITIAL_STATE); high_knowledge['knowledge'] = 85
    ok, reason = decision_is_available('advanced_challenge', high_knowledge)
    assert ok is True and reason is None

    assert decision_is_available('promotion', high_knowledge)[0] is False  # career still 0
    high_career = dict(INITIAL_STATE); high_career['career'] = 45
    assert decision_is_available('promotion', high_career)[0] is True

    high_money = dict(INITIAL_STATE); high_money['money'] = 2000
    assert decision_is_available('side_project', high_money)[0] is True

    assert decision_is_available('study', low_state)[0] is True   # normal decisions always open
    assert decision_is_available('nope', low_state)[0] is False


# ------------------------------------------------------------------
# create_branch end to end
# ------------------------------------------------------------------

def test_create_branch_full(app, user):
    root = _make_root(app, user)
    child = create_branch(root, 'study', user)
    st = child.get_state()
    assert st == apply_effects(INITIAL_STATE, DECISIONS['study']['effects'])
    # parent untouched
    assert root.get_state() == INITIAL_STATE
    # events: decision + consequence (no milestone at these stats)
    types = sorted(_types_of(app, child))
    assert types == ['consequence', 'decision'], types
    # Decision + Event rows recorded
    assert child.decisions.count() == 1
    # description reflects consequence
    assert child.description == DECISIONS['study']['consequence']

    tree = get_universe_tree(root)
    assert tree['children'][0]['id'] == child.id
    assert tree['score'] == calculate_reality_score(INITIAL_STATE)
    assert tree['energy'] == INITIAL_STATE['energy']
    assert tree['milestones'] == 0

    child2 = create_branch(root, 'go_out', user)
    assert child2.id != child.id  # siblings are independent rows, shared parent state base

    try:
        create_branch(_make_root(app, user), 'nope', user)
    except ValueError:
        pass
    else:
        assert False, 'create_branch with unknown decision should raise ValueError'


def test_create_branch_rejects_locked(app, user):
    root = create_root_universe(user)
    try:
        create_branch(root, 'advanced_challenge', user)
    except ValueError as e:
        assert 'Knowledge' in str(e)
    else:
        assert False, 'locked decision should raise ValueError'
    assert root.children.count() == 0  # nothing created


def test_create_branch_unlocks_special(app, user):
    root = create_root_universe(user)
    # study until knowledge >= 70 (50 + 15 per study -> 80)
    cur = root
    for _ in range(2):
        cur = create_branch(cur, 'study', user)
    assert cur.get_state()['knowledge'] >= 70
    avail = get_available_decisions(cur)
    adv = next(d for d in avail if d['key'] == 'advanced_challenge')
    assert adv['unlocked'] is True
    cur2 = create_branch(cur, 'advanced_challenge', user)
    assert cur2.get_state()['knowledge'] >= 90


def test_create_branch_milestone_events(app, user):
    root = create_root_universe(user)
    # study 2x: knowledge 50 -> 65 -> 80, crosses 75 => milestone
    cur = create_branch(root, 'study', user)
    cur2 = create_branch(cur, 'study', user)
    types = _types_of(app, cur2)
    assert 'milestone' in types, types
    # only one milestone event recorded
    assert types.count('milestone') == 1, types
    ms = Event.query.filter_by(universe_id=cur2.id, event_type='milestone').first()
    assert ms.description == 'Your knowledge has reached a new level.'


def test_create_branch_threshold_consequence_event(app, user):
    root = create_root_universe(user)
    # study twice: knowledge 50 -> 65 -> 80, crossing the >= 80 threshold
    cur = create_branch(root, 'study', user)
    cur = create_branch(cur, 'study', user)
    con = Event.query.filter_by(universe_id=cur.id, event_type='consequence').first()
    meta = con.meta_json
    assert meta is not None and 'opportunity' in meta, meta


def test_timeline_event_types(app, user):
    root = create_root_universe(user)
    a = create_branch(root, 'study', user)
    chain = get_universe_timeline(a)
    root_step = chain[0]
    assert root_step['events'][0]['type'] == 'creation'
    assert [e['type'] for e in root_step['events']] == ['creation']
    mid = next(s for s in chain if s['universe_id'] == a.id)
    types = [e['type'] for e in mid['events']]
    assert 'decision' in types and 'consequence' in types


def test_tree_metadata(app, user):
    root = _make_root(app, user)
    tree = get_universe_tree(root)
    assert 'score' in tree and 'energy' in tree and 'milestones' in tree
    assert tree['parent_id'] is None and tree['id'] == root.id


# ------------------------------------------------------------------
# routes via test client
# ------------------------------------------------------------------

def test_routes_csrf_and_branch(app, user):
    client = app.test_client()
    _login(client, app, user)
    root = create_root_universe(user)

    # universe page renders with new Step 7 data
    r = client.get('/universe/%d' % root.id)
    assert r.status_code == 200, r.status_code
    body = r.get_data(as_text=True)
    assert 'REALITY METRICS' in body
    assert 'WHAT WILL YOU DO IN THIS REALITY?' in body
    assert 'LOCKED' in body  # locked special decisions shown

    # missing CSRF -> 403
    r = client.post('/universe/%d/branch' % root.id, data={'decision': 'study'})
    assert r.status_code == 403, r.status_code

    # invalid CSRF -> 403
    r = client.post('/universe/%d/branch' % root.id,
                    data={'decision': 'study', '_csrf_token': 'bogus'})
    assert r.status_code == 403, r.status_code

    # locked decision even with valid CSRF -> no universe created
    before = Universe.query.count()
    r = client.post('/universe/%d/branch' % root.id,
                    data={'decision': 'advanced_challenge', '_csrf_token': 'testtoken'})
    assert r.status_code == 302, r.status_code
    assert Universe.query.count() == before

    # valid CSRF, valid decision -> new universe
    r = client.post('/universe/%d/branch' % root.id,
                    data={'decision': 'study', '_csrf_token': 'testtoken'})
    assert r.status_code == 302, r.status_code
    assert Universe.query.count() == before + 1
    child_id = int(r.headers['Location'].split('/')[-1])
    child = db.session.get(Universe, child_id)
    assert child.name == root.name + ' — Study'


def test_route_api_payload(app, user):
    client = app.test_client()
    _login(client, app, user)
    root = create_root_universe(user)
    r = client.get('/universe/%d/api' % root.id)
    assert r.status_code == 200
    data = r.get_json()
    assert 'reality_score' in data and 'reality_status' in data
    assert 'available_decisions' in data
    assert 'last_decision' in data and 'last_consequence' in data
    assert 'milestones_count' in data and 'events_count' in data
    assert data['reality_status'] == get_reality_status(data['reality_score'])


def test_route_ownership(app, user):
    user_a = _make_user(app, 'owner_a')
    other = _make_user(app, 'other_b')
    root = create_root_universe(user_a)
    client = app.test_client()
    _login(client, app, other)
    assert client.get('/universe/%d' % root.id).status_code == 403
    assert client.get('/universe/%d/api' % root.id).status_code == 403
    assert client.post('/universe/%d/branch' % root.id,
                       data={'decision': 'study'}).status_code == 403


def test_route_compare(app, user):
    client = app.test_client()
    _login(client, app, user)
    root = create_root_universe(user)
    a = create_branch(root, 'study', user)
    b = create_branch(root, 'work', user)
    r = client.get('/compare/%d/%d' % (a.id, b.id))
    assert r.status_code == 200, r.status_code
    body = r.get_data(as_text=True)
    assert 'REALITY SCORE' in body and 'SUMMARY' in body


def test_sibling_branching_flow(app, user):
    """Literal flow from the UX spec: siblings branch from the viewed reality."""
    root = create_root_universe(user)

    study = create_branch(root, 'study', user)     # START -> STUDY
    go_out = create_branch(root, 'go_out', user)   # back at START -> GO OUT
    work = create_branch(study, 'work', user)      # open STUDY -> WORK
    sleep = create_branch(root, 'sleep', user)     # back at START -> SLEEP

    # parent/child relationships
    assert study.parent_id == root.id
    assert go_out.parent_id == root.id
    assert sleep.parent_id == root.id
    assert work.parent_id == study.id

    # root has three siblings, STUDY has one child
    assert sorted(c.id for c in Universe.query.filter_by(parent_id=root.id).all()) == \
        sorted([study.id, go_out.id, sleep.id])
    assert sorted(c.id for c in Universe.query.filter_by(parent_id=study.id).all()) == [work.id]


def test_dev_style_tree(app, user):
    """Section 9-style test data shape (STUDY -> WORK, SLEEP; GO OUT -> PLAY GAME)."""
    root = create_root_universe(user)
    study = create_branch(root, 'study', user)
    create_branch(study, 'work', user)
    create_branch(study, 'sleep', user)
    go_out = create_branch(root, 'go_out', user)
    create_branch(go_out, 'play_game', user)

    assert sorted(c.name for c in Universe.query.filter_by(parent_id=root.id).all()) == \
        ['START — Go Out', 'START — Study']
    assert sorted(c.name for c in Universe.query.filter_by(parent_id=study.id).all()) == \
        ['START — Study — Sleep', 'START — Study — Work']
    assert sorted(c.name for c in Universe.query.filter_by(parent_id=go_out.id).all()) == \
        ['START — Go Out — Play Game']


def test_route_ux_context(app, user):
    client = app.test_client()
    _login(client, app, user)
    root = create_root_universe(user)
    study = create_branch(root, 'study', user)
    create_branch(study, 'work', user)      # STUDY has a child
    create_branch(root, 'go_out', user)     # STUDY has a sibling

    # child page: CURRENT + PARENT + CREATED FROM + OTHER PATHS + ALT PATHS
    r = client.get('/universe/%d' % study.id)
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert 'CURRENT REALITY' in body
    assert 'VIEW PARENT' in body
    assert 'OTHER PATHS FROM PARENT' in body
    assert 'ALTERNATE PATHS FROM THIS REALITY' in body
    assert 'Every decision creates another possible future.' in body
    assert 'CREATE REALITY' in body          # modal

    # root page: CURRENT + ALTERNATE PATHS (children), no PARENT block
    r = client.get('/universe/%d' % root.id)
    body = r.get_data(as_text=True)
    assert 'CURRENT REALITY' in body
    assert 'ALTERNATE PATHS FROM THIS REALITY' in body
    assert 'PARENT REALITY' not in body


def test_route_api_sidebar_fields(app, user):
    client = app.test_client()
    _login(client, app, user)
    root = create_root_universe(user)
    study = create_branch(root, 'study', user)

    r = client.get('/universe/%d/api' % study.id)
    assert r.status_code == 200
    d = r.get_json()
    assert d['parent_name'] == 'START'
    assert d['parent_id'] == root.id
    assert d['created_from'] == 'Study'
    assert d['created_at']
    assert type(d['children_count']) is int

    r = client.get('/universe/%d/api' % root.id)
    d = r.get_json()
    assert d['parent_name'] is None
    assert d['created_from'] is None


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------

def main():
    app, path = _new_app_with_tmp_db()
    with app.app_context():
        # one persistent session/context keeps committed instances usable
        user = _make_user(app, 'tester_main')
        check('score formula', test_score_formula)
        check('status thresholds', test_status_thresholds)
        check('normal consequence', test_consequence_normal)
        check('knowledge threshold consequence', test_consequence_threshold_knowledge)
        check('energy low consequence', test_consequence_threshold_energy_low)
        check('milestone purity / no dup in run', test_milestones_purity)
        check('milestone no recross', test_milestones_no_recross)
        check('compare summary text', test_reality_summary)
        check('effects clamping (floors/ceilings)', test_apply_effects_clamps)
        check('decision availability gates', test_decision_availability_gates)
        check('create_branch full lifecycle', lambda: test_create_branch_full(app, user))
        check('create_branch rejects locked special', lambda: test_create_branch_rejects_locked(app, user))
        check('special decision unlocks + applies', lambda: test_create_branch_unlocks_special(app, user))
        check('milestone event recorded exactly once', lambda: test_create_branch_milestone_events(app, user))
        check('threshold consequence recorded in events', lambda: test_create_branch_threshold_consequence_event(app, user))
        check('timeline event types', lambda: test_timeline_event_types(app, user))
        check('tree metadata (score/energy/milestones)', lambda: test_tree_metadata(app, user))
        check('csrf / branch route behavior', lambda: test_routes_csrf_and_branch(app, user))
        check('universe api payload', lambda: test_route_api_payload(app, user))
        check('universe ownership isolation', lambda: test_route_ownership(app, user))
        check('compare page render', lambda: test_route_compare(app, user))
        check('sibling branching flow (UX spec)', lambda: test_sibling_branching_flow(app, user))
        check('dev-style sibling tree shape', lambda: test_dev_style_tree(app, user))
        check('universe page reality context UX', lambda: test_route_ux_context(app, user))
        check('universe api sidebar fields', lambda: test_route_api_sidebar_fields(app, user))
    if os.path.exists(_TMP_DB):
        os.unlink(_TMP_DB)
    os.rmdir(_TMP_DIR)

    failed = [n for n, ok, _ in RESULTS if not ok]
    print('\n%d passed, %d failed' % (len(RESULTS) - len(failed), len(failed)))
    if failed:
        print('FAILED:', ', '.join(failed))
        sys.exit(1)


if __name__ == '__main__':
    main()
