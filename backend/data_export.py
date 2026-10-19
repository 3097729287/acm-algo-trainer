"""Explicit, read-only JSON export of the active account's learning journal."""
import json

from account_sync import TABLES, AccountStateSync, clean_profile
from training import iso


def export_data(training):
    # This allowlist deliberately excludes ranking authentication, translation
    # settings, browser documents/cookies and device state databases.
    with training.lock:
        existing = {row[0] for row in training.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        tables = {name: [dict(row) for row in training.connection.execute(
            f'SELECT * FROM "{name}" ORDER BY ' + ','.join(keys))] if name in existing else []
            for name, keys in TABLES.items()}
        tables['account_preferences'] = [row for row in tables['account_preferences']
                                         if row['key'] in ('ui', 'receipt-bindings')]
        for row in tables['account_preferences']:
            row['value'] = json.dumps(AccountStateSync._portable_json(json.loads(row['value'])), ensure_ascii=False)
        identity = training.connection.execute('SELECT nickname FROM ranking_profile WHERE singleton=1').fetchone()
        exported_at = iso(training._now())
    extensions = getattr(training.store, 'extensions', None)
    hub = extensions.snapshot() if callable(getattr(extensions, 'snapshot', None)) else {}
    from version import VERSION
    return {'format': 'tb-learning-export', 'formatVersion': 1, 'appVersion': VERSION,
            'exportedAt': exported_at, 'nickname': identity['nickname'] if identity else '',
            'tables': tables, 'publicAccounts': [clean_profile(row) for row in hub.get('accounts', [])]}
