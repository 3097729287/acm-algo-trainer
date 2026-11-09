"""Counting identity for one reviewed cross-site pair, never navigation URLs.

The exact complete-source proof is in
content-updates/20261109-new-xcpc-hubei/source-review.json#existingEquivalentTasks.
No title, tag, arbitrary metadata field or nearby problem number is evidence.
"""
import hashlib

PAIR_KEY = 'luogu.com.cn/problem/P10865'
PAIR_KEYS = (PAIR_KEY, 'codeforces.com/gym/105139/problem/H')
PAIR_IDS = ('luogu-training-P10865', 'remote:codeforces:105139::H')
PAIR_HASHES = tuple(hashlib.sha256(key.encode()).hexdigest() for key in PAIR_KEYS)


def question_key(value):
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    if value in (*PAIR_KEYS, *PAIR_IDS, *PAIR_HASHES):
        return PAIR_KEY
    # Lazy import avoids the existing insights/progression import cycle.
    from insights import canonical_url
    native = canonical_url(value)
    return PAIR_KEY if native in PAIR_KEYS else native


def question_alias_keys(value):
    key = question_key(value) or value
    return PAIR_KEYS if key == PAIR_KEY else ((key,) if key else ())


def annotate_question(row):
    key = question_key(row.get('url') or row.get('id'))
    if key == PAIR_KEY:
        row.update(questionKey=key, questionAliasKeys=list(PAIR_KEYS), questionAliasIds=list(PAIR_IDS))
    return row
