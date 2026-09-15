"""Deterministic, presentation-only guidance for the Reality Laboratory."""

STAT_LABELS = {
    'money': 'resources', 'energy': 'energy', 'knowledge': 'knowledge',
    'career': 'career momentum', 'relationships': 'connections',
}


def build_reality_insights(state, decision_count=0, branch_count=0):
    """Return truthful, repeatable insights derived only from persisted state."""
    values = {key: state.get(key, 0) for key in STAT_LABELS}
    lowest = min(values, key=values.get)
    highest = max(values, key=values.get)
    if values['energy'] <= 25:
        signal = 'LOW ENERGY SIGNAL'
        recommendation = 'Protect this timeline: choose recovery before another demanding path.'
    elif values['money'] <= 150:
        signal = 'RESOURCE PRESSURE'
        recommendation = 'This reality needs resources before it can safely support ambitious choices.'
    elif decision_count == 0:
        signal = 'ORIGIN READY'
        recommendation = 'Create two different first branches to see how this reality can diverge.'
    elif branch_count == 0:
        signal = 'SINGLE TIMELINE'
        recommendation = 'Return here and make a contrasting decision to reveal a meaningful fork.'
    else:
        signal = 'MULTIVERSE ACTIVE'
        recommendation = 'Compare parallel paths to find which trade-offs created the stronger reality.'
    return {
        'signal': signal,
        'recommendation': recommendation,
        'strength': 'Strongest signal: ' + STAT_LABELS[highest].title(),
        'tension': 'Watch closely: ' + STAT_LABELS[lowest].title(),
        'strongest_key': highest,
        'weakest_key': lowest,
    }
