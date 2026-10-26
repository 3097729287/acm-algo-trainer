"""Account-owned lists in the existing durable, synchronized preference journal."""
from contextlib import closing
import json
import re
import sqlite3
import uuid
from training import ServiceError, iso

PREFIX = 'custom-training-list:'


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
    ids = body.get('problemIds', [])
    if not isinstance(title, str) or not body.get('deleted') and (not 1 <= len(title.strip()) <= 80 or re.search(r'[\x00-\x1f\x7f]', title)):
        raise ServiceError(400, '题单名称须为 1～80 个字符')
    if not isinstance(ids, list) or len(ids) > 1000 or any(not isinstance(item, str) or not 0 < len(item) <= 512 for item in ids):
        raise ServiceError(400, '每份题单最多添加 1000 道题')
    with training.lock:
        existing = training.connection.execute('SELECT value FROM account_preferences WHERE key=?', (PREFIX + identity,)).fetchone()
        if body.get('id') and not existing:
            raise ServiceError(404, '没有找到这份题单')
        if not existing and len(read_lists(training)) >= 100:
            raise ServiceError(400, '最多创建 100 份题单')
        problems = []
        for item in dict.fromkeys(ids):
            row = training._row(item)
            problems.append({'problemId': item, 'pid': row.get('problem') or item, 'url': row.get('url'), 'sections': []})
        value = {'id':identity,'title':title.strip(),'custom':True,'available':True,'aggregateChildren':False,
                 'children':[],'problems':problems,'categories':[{'id':'personal','name':'我的题单','order':-1,'position':0}],
                 'topicPath':['我的题单'],'deleted':bool(body.get('deleted'))}
        with training._write() as db:
            db.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
                       (PREFIX + identity, json.dumps(value, ensure_ascii=False), iso(training._now())))
    return {'list':value, 'customLists':read_lists(training)}
