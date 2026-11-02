"""Keep an explicitly requested account history cutoff across old snapshots."""
import copy
import json
from progression import parse_time

KEY = 'submission-history-cutoff-v1'


def marker(value, owner):
    try:
        value = json.loads(value) if isinstance(value, str) else value
        if not isinstance(value, dict) or value.get('version') != 1 or value.get('owner', owner) != owner:
            return None
        before = parse_time(value.get('before'))
        if before is None:
            return None
        return value
    except (ValueError, TypeError, AttributeError):
        return None


def preserve(training, state):
    owner = training._ranking_profile()['user_id']
    local = training.connection.execute('SELECT * FROM account_preferences WHERE key=?', (KEY,)).fetchone()
    remote = next((row for row in state['tables'].get('account_preferences', []) if row.get('key') == KEY), None)
    candidates = [dict(row) for row in (local, remote) if row and marker(row['value'], owner)]
    if not candidates:
        return state, False
    chosen = max(candidates, key=lambda row: parse_time(marker(row['value'], owner)['before']))
    cutoff = parse_time(marker(chosen['value'], owner)['before'])
    result = copy.deepcopy(state)
    records = result['tables'].get('submissions', [])
    kept = [row for row in records if not (parse_time(row.get('submitted_at')) and parse_time(row['submitted_at']) < cutoff)]
    deleted = {row['id'] for row in records} - {row['id'] for row in kept}
    result['tables']['submissions'] = kept
    preferences = result['tables'].get('account_preferences', [])
    result['tables']['account_preferences'] = [row for row in preferences if row.get('key') != KEY
        and row.get('key') not in {'review-receipt:' + identity for identity in deleted}] + [chosen]
    return result, bool(deleted or chosen != remote)
