"""Private list labels, synchronized in the existing account preference journal."""
import json
import re
import unicodedata
import sqlite3
from contextlib import closing
from training import ServiceError, iso

PREFIX = 'training-list-tags:'


def _index(training):
    records = tuple(tuple(row) for row in training.connection.execute(
        'SELECT key,value FROM account_preferences WHERE key LIKE ? ORDER BY key', (PREFIX + '%',)))
    if getattr(training, '_list_tag_signature', None) == records:
        return
    db = training.connection
    db.execute('CREATE TEMP TABLE IF NOT EXISTS list_tag_index(list_id TEXT NOT NULL,tag TEXT NOT NULL,PRIMARY KEY(list_id,tag))')
    db.execute('CREATE INDEX IF NOT EXISTS temp.list_tags_by_tag ON list_tag_index(tag,list_id)')
    db.execute('DELETE FROM list_tag_index')
    for key, raw in records:
        try:
            tags = json.loads(raw)
        except (ValueError, TypeError):
            continue
        if isinstance(tags, list):
            db.executemany('INSERT OR IGNORE INTO list_tag_index VALUES (?,?)',
                           [(key[len(PREFIX):], tag) for tag in tags if isinstance(tag, str) and 0 < len(tag) <= 24])
    training._list_tag_signature = records


def read_tags(training, tag=None, *, independent=False):
    if independent:
        # A committed read-only snapshot avoids waiting for long statistics or
        # judging work holding the shared personal connection. The HTTP account
        # barrier still binds this file to the authenticated user.
        with closing(sqlite3.connect(training.db_path.resolve().as_uri() + '?mode=ro', uri=True, timeout=5)) as db:
            records = db.execute('SELECT key,value FROM account_preferences WHERE key LIKE ? ORDER BY key', (PREFIX + '%',)).fetchall()
        result = {}
        for key, raw in records:
            try:
                labels = json.loads(raw)
            except (ValueError, TypeError):
                continue
            if isinstance(labels, list):
                labels = sorted({label for label in labels if isinstance(label, str) and 0 < len(label) <= 24})
                if labels:
                    result[key[len(PREFIX):]] = labels
        return {'tags': result, **({'listIds': [identity for identity, labels in result.items() if tag in labels]} if tag is not None else {})}
    with training.lock:
        _index(training)
        result = {}
        for identity, label in training.connection.execute('SELECT list_id,tag FROM list_tag_index ORDER BY list_id,tag'):
            result.setdefault(identity, []).append(label)
        value = {'tags': result}
        if tag is not None:
            value['listIds'] = [row[0] for row in training.connection.execute('SELECT list_id FROM list_tag_index WHERE tag=? ORDER BY list_id', (tag,))]
        return value


def save_tags(training, body, list_ids):
    if not isinstance(body, dict) or set(body) != {'listId', 'tags'}:
        raise ServiceError(400, '题单标签格式无效')
    identity, tags = body['listId'], body['tags']
    if not isinstance(identity, str) or len(identity) > 160 or (identity not in list_ids and not re.fullmatch(r'curriculum:(?:\d{1,2}|(?:08|09):[^\x00-\x1f]{1,48})', identity)):
        raise ServiceError(400, '没有找到对应题单')
    if not isinstance(tags, list) or len(tags) > 16 or any(not isinstance(tag, str) for tag in tags):
        raise ServiceError(400, '每份题单最多设置 16 个自定义标签')
    tags = list(dict.fromkeys(unicodedata.normalize('NFKC', tag).strip() for tag in tags))
    if any(not tag or len(tag) > 24 or re.search(r'[\x00-\x1f\x7f-\x9f]', tag) for tag in tags):
        raise ServiceError(400, '每个标签须为 1～24 个字符')
    with training.lock:
        with training._write() as db:
            # An empty list is a synchronized deletion, so older devices cannot
            # resurrect labels merely because their row was absent locally.
            db.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
                       (PREFIX + identity, json.dumps(tags, ensure_ascii=False), iso(training._now())))
        return read_tags(training)
