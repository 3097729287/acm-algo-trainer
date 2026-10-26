"""Account-owned lists in the existing durable, synchronized preference journal."""
from contextlib import closing
import json
import re
import sqlite3
import uuid
from training import ServiceError, iso
from insights import canonical_url

PREFIX = 'custom-training-list:'
MAX_PROBLEMS = 20000


def _problem_ids(ids):
    if not isinstance(ids, list) or len(ids) > MAX_PROBLEMS or any(not isinstance(item, str) or not 0 < len(item) <= 512 for item in ids):
        raise ServiceError(400, f'每份题单最多添加 {MAX_PROBLEMS} 道题')
    return list(dict.fromkeys(ids))


def _problems(training, ids):
    # Resolve a batch against one catalogue, including aliases, instead of
    # repeatedly loading it for each problem and each destination list.
    catalog = {identity: row for row in training._library() for identity in [row['id'], *row.get('aliasIds', [])]}
    result, seen = [], set()
    for identity in ids:
        row = catalog.get(identity) or training._row(identity)
        key = canonical_url(row.get('url')) or row['id']
        if key not in seen:
            seen.add(key)
            result.append({'problemId': row['id'], 'pid': row.get('problem') or row['id'], 'url': row.get('url'), 'sections': []})
    return result


def _existing(training, identity):
    if not isinstance(identity, str) or not re.fullmatch(r'custom:[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', identity):
        raise ServiceError(400, '题单编号无效')
    record = training.connection.execute('SELECT value FROM account_preferences WHERE key=?', (PREFIX + identity,)).fetchone()
    value = json.loads(record[0]) if record else None
    if not isinstance(value, dict) or value.get('deleted') or not value.get('custom'):
        raise ServiceError(404, '没有找到这份题单')
    return value


def _write_lists(training, values):
    if not values:
        return
    with training._write() as db:
        db.executemany('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
                       [(PREFIX + value['id'], json.dumps(value, ensure_ascii=False), iso(training._now())) for value in values])


def add_problems(training, body):
    if not isinstance(body, dict) or set(body) != {'listIds', 'problemIds'}:
        raise ServiceError(400, '题单格式无效')
    identities = body['listIds']
    if not isinstance(identities, list) or not 1 <= len(identities) <= 100 or any(not isinstance(item, str) for item in identities):
        raise ServiceError(400, '请选择自建题单')
    ids = _problem_ids(body['problemIds'])
    if not ids:
        raise ServiceError(400, '没有匹配的题目')
    with training.lock:
        values = [_existing(training, identity) for identity in dict.fromkeys(identities)]
        problems = _problems(training, ids)
        added = {}
        for value in values:
            existing_ids = {item.get('problemId') for item in value['problems']}
            existing_urls = {canonical_url(item.get('url')) for item in value['problems'] if item.get('url')}
            additions = [item for item in problems if item['problemId'] not in existing_ids and (not item.get('url') or canonical_url(item['url']) not in existing_urls)]
            value['problems'] = value['problems'] + additions
            if len(value['problems']) > MAX_PROBLEMS:
                raise ServiceError(400, f'每份题单最多添加 {MAX_PROBLEMS} 道题')
            added[value['id']] = len(additions)
        # Validate every destination first: failures never leave a partial batch.
        _write_lists(training, [value for value in values if added[value['id']]])
    return {'customLists': read_lists(training), 'added': added}


def read_lists(training):
    with closing(sqlite3.connect(training.db_path.resolve().as_uri() + '?mode=ro', uri=True, timeout=5)) as db:
        records = db.execute('SELECT value FROM account_preferences WHERE key LIKE ? ORDER BY updated_at DESC,key', (PREFIX + '%',)).fetchall()
    result = []
    for record in records:
        try:
            value = json.loads(record[0])
        except (ValueError, TypeError):
            continue
        if isinstance(value, dict) and not value.get('deleted') and isinstance(value.get('problems'), list):
            result.append(value)
    return result


def save_list(training, body):
    if not isinstance(body, dict) or set(body) - {'id', 'title', 'problemIds', 'deleted'}:
        raise ServiceError(400, '题单格式无效')
    identity = body.get('id') or 'custom:' + str(uuid.uuid4())
    if not isinstance(identity, str) or not re.fullmatch(r'custom:[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', identity):
        raise ServiceError(400, '题单编号无效')
    if body.get('deleted') not in (None, True, False):
        raise ServiceError(400, '题单格式无效')
    title = body.get('title', '')
    ids = _problem_ids(body.get('problemIds', []))
    if not isinstance(title, str) or not body.get('deleted') and (not 1 <= len(title.strip()) <= 80 or re.search(r'[\x00-\x1f\x7f]', title)):
        raise ServiceError(400, '题单名称须为 1～80 个字符')
    with training.lock:
        existing = _existing(training, identity) if body.get('id') else None
        if body.get('deleted') and not existing:
            raise ServiceError(404, '没有找到这份题单')
        if not existing and len(read_lists(training)) >= 100:
            raise ServiceError(400, '最多创建 100 份题单')
        problems = _problems(training, ids) if ids else []
        value = {'id':identity,'title':title.strip(),'custom':True,'available':True,'aggregateChildren':False,
                 'children':[],'problems':problems,'categories':[{'id':'personal','name':'我的题单','order':-1,'position':0}],
                 'topicPath':['我的题单'],'deleted':bool(body.get('deleted'))}
        if body.get('deleted'):
            value = {**existing, 'deleted': True}
        _write_lists(training, [value])
    return {'list':value, 'customLists':read_lists(training)}
