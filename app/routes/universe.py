import json

from flask import Blueprint, render_template, request, redirect, jsonify, abort, url_for, flash

from app import db
from app.models import Universe, Event
from app.services.auth_service import login_required, get_owned_universe, validate_csrf_token
from app.services.universe_service import (
    DECISIONS,
    create_branch,
    get_universe_tree,
    get_root_universe,
    get_universe_timeline,
    get_available_decisions,
)
from app.services.consequence_service import (
    calculate_reality_score,
    get_reality_status,
    get_reality_summary,
)
from app.services.insight_service import build_reality_insights

bp = Blueprint('universe', __name__)


@bp.route('/universe/<int:universe_id>')
@login_required
def view_universe(user, universe_id):
    universe = get_owned_universe(universe_id, user)

    parent = db.session.get(Universe, universe.parent_id) if universe.parent_id else None

    events = Event.query.filter_by(universe_id=universe.id).order_by(Event.created_at.asc()).all()
    last_event = events[-1] if events else None
    last_decision_effects = None
    last_decision_label = None
    last_consequence = None
    if last_event and last_event.meta_json:
        meta = json.loads(last_event.meta_json)
        last_decision_effects = meta.get('effects')
        last_decision_label = meta.get('decision')

    consequence_events = [e for e in events if e.event_type == 'consequence']
    if consequence_events:
        con = consequence_events[-1]
        last_consequence = {'description': con.description}
        if con.meta_json:
            meta = json.loads(con.meta_json)
            last_consequence['title'] = meta.get('title')
            last_consequence['type'] = meta.get('consequence_type')

    state = universe.get_state()
    score = calculate_reality_score(state)
    status = get_reality_status(score)
    milestones_count = sum(1 for e in events if e.event_type == 'milestone')
    decisions_count = sum(1 for e in events if e.event_type == 'decision')

    children = Universe.query.filter_by(parent_id=universe.id).order_by(Universe.created_at.asc()).all()
    children_info = [{
        'id': c.id, 'name': c.name,
        'decision': c.decisions.first().choice if c.decisions.first() else None,
        'score': calculate_reality_score(c.get_state()),
        'status': get_reality_status(calculate_reality_score(c.get_state())),
    } for c in children]

    created_from = None
    siblings_info = []
    if parent:
        decision_rec = universe.decisions.first()
        created_from = decision_rec.choice if decision_rec else None
        siblings = Universe.query.filter(
            Universe.parent_id == parent.id, Universe.id != universe.id
        ).order_by(Universe.created_at.asc()).all()
        siblings_info = [{
            'id': s.id, 'name': s.name,
            'decision': s.decisions.first().choice if s.decisions.first() else None,
            'score': calculate_reality_score(s.get_state()),
            'status': get_reality_status(calculate_reality_score(s.get_state())),
        } for s in siblings]

    changes = []
    if parent:
        parent_state = parent.get_state()
        labels = {'money': 'Money', 'energy': 'Energy', 'knowledge': 'Knowledge',
                  'career': 'Career', 'relationships': 'Relationships'}
        for key, label in labels.items():
            before, after = parent_state.get(key, 0), universe.get_state().get(key, 0)
            if before != after:
                changes.append({'key': key, 'label': label, 'before': before,
                                'after': after, 'delta': after - before})

    available = get_available_decisions(universe)
    decisions_json = json.dumps([{
        'key': d['key'],
        'label': d['label'],
        'effects': d['effects'],
        'consequence': d['consequence'],
        'unlocked': d['unlocked'],
        'unlock_reason': d['unlock_reason'],
    } for d in available])

    return render_template('universe.html',
                           universe=universe,
                           state=state,
                           parent=parent,
                           created_from=created_from,
                           children_info=children_info,
                           siblings_info=siblings_info,
                           available_decisions=available,
                           decisions_json=decisions_json,
                           last_event=last_event,
                           last_decision_effects=last_decision_effects,
                           last_decision_label=last_decision_label,
                           last_consequence=last_consequence,
                           reality_score=score,
                           reality_status=status,
                           insights=build_reality_insights(state, decisions_count, len(children_info)),
                           state_changes=changes,
                           milestones_count=milestones_count,
                           decisions_count=decisions_count,
                           events_count=len(events))


@bp.route('/universe/<int:universe_id>/branch', methods=['POST'])
@login_required
def branch_universe(user, universe_id):
    validate_csrf_token()
    universe = get_owned_universe(universe_id, user)

    decision_key = request.form.get('decision')
    if not decision_key or decision_key not in DECISIONS:
        flash('That decision is not available in this reality.', 'error')
        abort(400)

    try:
        child = create_branch(universe, decision_key, user)
    except PermissionError:
        abort(403)
    except ValueError as e:
        flash(str(e) or 'That decision is not available in this reality.', 'error')
        return redirect(url_for('universe.view_universe', universe_id=universe.id))

    flash('Your choice created a new timeline.', 'success')
    return redirect(url_for('universe.view_universe', universe_id=child.id))


@bp.route('/universe/<int:universe_id>/tree')
@login_required
def universe_tree_page(user, universe_id):
    universe = get_owned_universe(universe_id, user)
    return render_template('tree.html', universe=universe)


@bp.route('/universe/<int:universe_id>/tree.json')
@login_required
def universe_tree_json(user, universe_id):
    universe = get_owned_universe(universe_id, user)
    root = get_root_universe(universe)
    if root.user_id != user.id:
        abort(403)
    tree = get_universe_tree(root)
    return jsonify(tree)


@bp.route('/universe/<int:universe_id>/timeline.json')
@login_required
def universe_timeline_json(user, universe_id):
    universe = get_owned_universe(universe_id, user)
    timeline = get_universe_timeline(universe)
    for step in timeline:
        u = db.session.get(Universe, step['universe_id'])
        if u and u.user_id != user.id:
            abort(403)
    return jsonify(timeline)


@bp.route('/universe/<int:universe_id>/api')
@login_required
def universe_api(user, universe_id):
    universe = get_owned_universe(universe_id, user)

    state = universe.get_state()
    events = Event.query.filter_by(universe_id=universe.id).order_by(Event.created_at.asc()).all()
    last_decision = None
    last_consequence = None
    for e in reversed(events):
        if e.event_type == 'decision' and last_decision is None:
            last_decision = e.description
        if e.event_type == 'consequence' and last_consequence is None:
            meta = json.loads(e.meta_json) if e.meta_json else {}
            last_consequence = {
                'description': e.description,
                'title': meta.get('title'),
                'type': meta.get('consequence_type'),
            }

    parent = db.session.get(Universe, universe.parent_id) if universe.parent_id else None
    child_count = Universe.query.filter_by(parent_id=universe.id).count()
    created_from = None
    if parent:
        decision_rec = universe.decisions.first()
        created_from = decision_rec.choice if decision_rec else None

    return jsonify({
        'id': universe.id,
        'name': universe.name,
        'description': universe.description,
        'parent_id': universe.parent_id,
        'parent_name': parent.name if parent else None,
        'created_at': universe.created_at.strftime('%b %d, %Y') if universe.created_at else None,
        'created_from': created_from,
        'children_count': child_count,
        'state': state,
        'available_decisions': get_available_decisions(universe),
        'reality_score': calculate_reality_score(state),
        'reality_status': get_reality_status(calculate_reality_score(state)),
        'last_decision': last_decision,
        'last_consequence': last_consequence,
        'milestones_count': sum(1 for e in events if e.event_type == 'milestone'),
        'events_count': len(events),
    })
