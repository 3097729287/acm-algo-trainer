"""Account-owned starting programs, separate from algorithm snippets."""
import json
import re
import uuid

from training import ServiceError, iso

PREFIX = 'initial-code:'
SELECTION = 'initial-code-selection:'
MAX_CODE_BYTES = 64 * 1024
DEFAULTS = {
    'cpp17': '#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n\n    \n    return 0;\n}\n',
    'python3': 'import sys\n\ndef solve():\n    pass\n\nif __name__ == "__main__":\n    solve()\n',
}


def _language(value):
    if not isinstance(value, str) or value not in DEFAULTS:
        raise ServiceError(400, '编程语言无效')
    return value


def _read(training, key):
    row = training.connection.execute('SELECT value FROM account_preferences WHERE key=?', (key,)).fetchone()
    return json.loads(row['value']) if row else None


def _write(training, db, key, value):
    db.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
               (key, json.dumps(value, ensure_ascii=False, sort_keys=True), iso(training._now())))


def _owned(training):
    return sorted((value for row in training.connection.execute("SELECT value FROM account_preferences WHERE key LIKE 'initial-code:%'")
                   if isinstance(value := json.loads(row['value']), dict) and not value.get('deleted')),
                  key=lambda value: (value['title'].casefold(), value['id']))


def _default(language):
    return {'id': 'default', 'title': '默认', 'language': language, 'code': DEFAULTS[language], 'builtin': True}


def selected(training):
    """Small private payload for the workbench, leaving every draft untouched."""
    with training.lock:
        choices, revisions, templates = {}, {}, []
        for language in DEFAULTS:
            choice = _read(training, SELECTION + language) or {}
            identity = choice.get('id', 'default')
            value = _read(training, identity) if isinstance(identity, str) and re.fullmatch(PREFIX + r'[a-f0-9]{32}', identity) else None
            if not value or value.get('deleted') or value.get('language') != language:
                value = _default(language)
            choices[language] = value['id']
            revisions[language] = choice.get('revision', '')
            templates.append(value)
        return {'selection': choices, 'revisions': revisions, 'templates': templates}


def catalog(training):
    with training.lock:
        return {**selected(training), 'templates': [_default(language) for language in DEFAULTS] + _owned(training)}


def choose(training, body):
    if not isinstance(body, dict) or set(body) != {'id', 'language', 'revision'}:
        raise ServiceError(400, '初始代码模板选择无效')
    language = _language(body['language'])
    identity = body['id']
    if not isinstance(identity, str) or identity != 'default' and not re.fullmatch(PREFIX + r'[a-f0-9]{32}', identity):
        raise ServiceError(400, '初始代码模板无效')
    with training.lock:
        if identity != 'default':
            value = _read(training, identity)
            if not value or value.get('deleted') or value.get('language') != language:
                raise ServiceError(404, '没有找到这个初始代码模板')
        previous = _read(training, SELECTION + language) or {}
        if body['revision'] != previous.get('revision', ''):
            raise ServiceError(409, '初始代码模板已在其它位置修改，请重新读取后选择')
        if previous.get('id', 'default') != identity:
            with training._write() as db:
                _write(training, db, SELECTION + language, {'id': identity, 'revision': uuid.uuid4().hex})
        return catalog(training)


def save(training, body):
    if not isinstance(body, dict) or set(body) - {'id', 'title', 'language', 'code', 'revision', 'delete'}:
        raise ServiceError(400, '初始代码模板格式无效')
    identity = body.get('id')
    if identity is not None and (not isinstance(identity, str) or not re.fullmatch(PREFIX + r'[a-f0-9]{32}', identity)):
        raise ServiceError(400, '默认模板请另存为自己的模板')
    if type(body.get('delete', False)) is not bool:
        raise ServiceError(400, '初始代码模板操作无效')
    with training.lock:
        previous = _read(training, identity) if identity else None
        if identity and (not previous or previous.get('deleted')):
            raise ServiceError(404, '没有找到这个初始代码模板')
        if previous and body.get('revision') != previous.get('revision'):
            raise ServiceError(409, '初始代码模板已在其它位置修改，请重新读取后保存')
        if body.get('delete'):
            if not previous:
                raise ServiceError(404, '没有找到这个初始代码模板')
            value = {**previous, 'deleted': True, 'revision': uuid.uuid4().hex, 'updatedAt': iso(training._now())}
        else:
            title, code = body.get('title'), body.get('code')
            language = _language(body.get('language'))
            if (not isinstance(title, str) or not title.strip() or len(title.encode('utf8')) > 120
                    or any(ord(char) < 32 for char in title) or not isinstance(code, str)
                    or '\x00' in code or len(code.encode('utf8')) > MAX_CODE_BYTES):
                raise ServiceError(400, '请填写模板名称，代码不得超过 64 KiB')
            if previous and previous['language'] != language:
                raise ServiceError(400, '请为其它语言另建模板')
            if previous is None and len(_owned(training)) >= 32:
                raise ServiceError(400, '初始代码模板已达 32 个，请先整理已有模板')
            value = {'id': identity or PREFIX + uuid.uuid4().hex, 'title': title.strip(), 'language': language,
                     'code': code, 'builtin': False, 'revision': uuid.uuid4().hex,
                     'createdAt': previous['createdAt'] if previous else iso(training._now()), 'updatedAt': iso(training._now())}
        with training._write() as db:
            _write(training, db, value['id'], value)
            if value.get('deleted'):
                key = SELECTION + value['language']
                current = _read(training, key) or {}
                if current.get('id') == value['id']:
                    _write(training, db, key, {'id': 'default', 'revision': uuid.uuid4().hex})
        return {**catalog(training), 'template': value}
