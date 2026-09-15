"""consequence_service.py — deterministic consequences, milestones, reality metrics.

This module is deliberately free of database writes. Every function is pure and
derives its results from the state values it receives.
"""


def _clamp(value, low=0, high=100):
    return max(low, min(high, value))


def calculate_reality_score(state):
    """Derive a 0-100 reality score from the current state. Never stored.

    Money is normalised over a 0-3000 range; the other four stats are already
    0-100. The five scores are averaged.
    """
    if not state:
        return 0
    money = _clamp(state.get('money', 0), 0, 3000) / 30.0
    energy = _clamp(state.get('energy', 0))
    knowledge = _clamp(state.get('knowledge', 0))
    career = _clamp(state.get('career', 0))
    relationships = _clamp(state.get('relationships', 0))
    return round((money + energy + knowledge + career + relationships) / 5)


def get_reality_status(score):
    """Presentation-only label derived from a reality score."""
    if score <= 25:
        return 'Fragile Reality'
    if score <= 50:
        return 'Unstable Reality'
    if score <= 75:
        return 'Balanced Reality'
    if score <= 90:
        return 'Thriving Reality'
    return 'Exceptional Reality'


# Threshold-based consequences.
# (stat, direction, threshold, type, title, description)
# direction 'gte' fires when the stat reaches/exceeds threshold from below,
# direction 'lte' fires when the stat falls to/below threshold from above.
THRESHOLD_CONSEQUENCES = [
    ('knowledge', 'gte', 80, 'opportunity', 'New Opportunity',
     'Your growing knowledge has opened a new path.'),
    ('career', 'gte', 50, 'career_momentum', 'Career Momentum',
     'Your career is beginning to accelerate.'),
    ('relationships', 'gte', 70, 'strong_connections', 'Strong Connections',
     'Your social circle is becoming an important part of your life.'),
    ('energy', 'lte', 20, 'running_low', 'Running Low',
     'You are pushing yourself too hard.'),
    ('money', 'gte', 2000, 'financial_freedom', 'Financial Freedom',
     'You now have enough savings to consider different opportunities.'),
    ('money', 'lte', 1, 'financial_strain', 'Financial Strain',
     'Your finances are running thin.'),
    ('energy', 'lte', 1, 'exhaustion', 'Exhausted',
     'You are completely spent.'),
]


def _crossed(stat, direction, threshold, old_state, new_state):
    old = old_state.get(stat, 0)
    new = new_state.get(stat, 0)
    if direction == 'gte':
        return new >= threshold and old < threshold
    return new <= threshold and old > threshold


def evaluate_consequence(decision_key, old_state, new_state):
    """Return structured consequence info for a decision.

    Returns dict with: title, description, type, effects.
    The normal consequence comes from the decision's own narrative; when a
    notable threshold is newly crossed the consequence type reflects it.
    """
    from app.services.universe_service import DECISIONS  # deferred to avoid cycle

    cfg = DECISIONS.get(decision_key, {})
    description = cfg.get('consequence') or cfg.get('description', '')
    con_type = 'effect'
    extra = ''
    for stat, direction, threshold, ctype, ctitle, cdesc in THRESHOLD_CONSEQUENCES:
        if _crossed(stat, direction, threshold, old_state, new_state):
            con_type = ctype
            con_title = ctitle
            extra = cdesc
            break

    if con_type != 'effect':
        description = (description + ' ' + extra).strip()
        return {
            'title': con_title,
            'description': description,
            'type': con_type,
            'effects': cfg.get('effects', {}),
        }

    return {
        'title': cfg.get('label', decision_key),
        'description': description,
        'type': con_type,
        'effects': cfg.get('effects', {}),
    }


def generate_consequence(decision_key, old_state, new_state):
    """Alias for evaluate_consequence with the required signature."""
    return evaluate_consequence(decision_key, old_state, new_state)


MILESTONE_RULES = [
    ('knowledge', 75, 'Knowledge Milestone', 'Your knowledge has reached a new level.'),
    ('career', 50, 'Career Milestone', 'Your career has reached a new level.'),
    ('relationships', 75, 'Social Milestone', 'Your social circle has strengthened.'),
    ('energy', 90, 'Well Rested', 'Your energy is at a peak.'),
    ('money', 2000, 'Financial Milestone', 'Your savings have grown significantly.'),
]


def evaluate_milestones(old_state, new_state):
    """Return a list of milestones newly crossed between old and new state.

    A milestone is only reported when its threshold is crossed for the first
    time (old below threshold, new at/above threshold). Pure function.
    """
    milestones = []
    for stat, threshold, title, description in MILESTONE_RULES:
        if new_state.get(stat, 0) >= threshold and old_state.get(stat, 0) < threshold:
            milestones.append({
                'type': stat,
                'threshold': threshold,
                'title': title,
                'description': description,
            })
    return milestones


def get_reality_summary(state_a, state_b):
    """Deterministic one-line comparison summary between two universes."""
    stats = ['knowledge', 'career', 'relationships', 'energy', 'money']
    label_map = {
        'knowledge': 'knowledge',
        'career': 'career',
        'relationships': 'relationships',
        'energy': 'energy',
        'money': 'money',
    }
    a_pos = [s for s in stats if state_a.get(s, 0) > state_b.get(s, 0)]
    b_pos = [s for s in stats if state_b.get(s, 0) > state_a.get(s, 0)]

    if not a_pos and not b_pos:
        return 'Universe A and Universe B are identical in every field.'

    a_focus = ', '.join(label_map[s] for s in a_pos[:2])
    b_focus = ', '.join(label_map[s] for s in b_pos[:2])
    parts = []
    if a_focus:
        parts.append('Universe A is stronger in ' + a_focus + '.')
    if b_focus:
        parts.append('Universe B is stronger in ' + b_focus + '.')
    return ' '.join(parts)