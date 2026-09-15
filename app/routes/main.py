from flask import Blueprint, render_template, request, redirect, flash, abort
from sqlalchemy import func
from flask import url_for

from app import db
from app.models import Universe, Event
from app.services.auth_service import login_required, get_current_user, get_owned_universe, generate_csrf_token
from app.services.universe_service import (
    create_root_universe,
    INITIAL_STATE,
)
from app.services.consequence_service import (
    calculate_reality_score,
    get_reality_status,
    get_reality_summary,
)
from app.services.insight_service import build_reality_insights

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_universe(user):
    if request.method == 'POST':
        from app.services.auth_service import validate_csrf_token
        validate_csrf_token()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        if not name:
            flash('Universe name is required.', 'error')
            return render_template('create.html', initial_state=INITIAL_STATE)
        if len(name) > 100:
            flash('Universe name is too long.', 'error')
            return render_template('create.html', initial_state=INITIAL_STATE)

        universe = create_root_universe(user, name=name, description=description or None)
        flash('REALITY CREATED', 'success')
        return redirect(url_for('universe.view_universe', universe_id=universe.id))

    return render_template('create.html', initial_state=INITIAL_STATE)


@bp.route('/universes')
@login_required
def list_universes(user):
    roots = Universe.query.filter_by(user_id=user.id, parent_id=None).order_by(Universe.created_at.desc()).all()
    universe_data = []
    for u in roots:
        universe_data.append({
            'universe': u,
            'child_count': Universe.query.filter_by(parent_id=u.id).count(),
            'decision_count': u.decisions.count(),
            'score': calculate_reality_score(u.get_state()),
            'status': get_reality_status(calculate_reality_score(u.get_state())),
        })
    all_realities = Universe.query.filter_by(user_id=user.id).all()
    scores = [calculate_reality_score(u.get_state()) for u in all_realities]
    branches = sum(Universe.query.filter_by(parent_id=u.id).count() for u in all_realities)
    profile = {
        'reality_count': len(all_realities), 'branch_count': branches,
        'highest_score': max(scores) if scores else 0,
    }
    return render_template('universes.html', universes=universe_data, profile=profile)


@bp.route('/explore')
@login_required
def explore(user):
    """A flat, navigable index for every reality owned by the current user."""
    realities = Universe.query.filter_by(user_id=user.id).order_by(Universe.created_at.desc()).all()
    options = [{
        'universe': u,
        'score': calculate_reality_score(u.get_state()),
        'status': get_reality_status(calculate_reality_score(u.get_state())),
    } for u in realities]
    return render_template('explore.html', realities=options)


@bp.route('/compare/<int:id1>/<int:id2>')
@login_required
def compare(user, id1, id2):
    u1 = get_owned_universe(id1, user)
    u2 = get_owned_universe(id2, user)

    e1 = Event.query.filter_by(universe_id=u1.id).order_by(Event.created_at.desc()).first()
    e2 = Event.query.filter_by(universe_id=u2.id).order_by(Event.created_at.desc()).first()

    state_a = u1.get_state()
    state_b = u2.get_state()
    score_a = calculate_reality_score(state_a)
    score_b = calculate_reality_score(state_b)

    return render_template('compare.html',
                           universe_a=u1, universe_b=u2,
                           state_a=state_a, state_b=state_b,
                           last_event_a=e1, last_event_b=e2,
                           score_a=score_a, score_b=score_b,
                           status_a=get_reality_status(score_a),
                           status_b=get_reality_status(score_b),
                           summary=get_reality_summary(state_a, state_b))
