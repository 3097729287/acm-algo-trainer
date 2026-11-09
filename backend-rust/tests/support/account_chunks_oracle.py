"""Test-only synthetic graph oracle. Production Rust never invokes this script."""
from __future__ import annotations
import base64
import datetime as dt
import hashlib
import json
import math
import random
from pathlib import Path
import sqlite3
import struct
import sys
import threading
from types import SimpleNamespace

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'backend'))
import account_chunks as chunks
from account_sync import TABLES


class CountingLock:
    def __init__(self):
        self.lock = threading.Lock()
        self.held = False
    def __enter__(self):
        self.lock.acquire()
        self.held = True
    def __exit__(self, *_):
        self.held = False
        self.lock.release()


def transport():
    result = chunks.ChunkTransport.__new__(chunks.ChunkTransport)
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    db.executescript('CREATE TABLE account_sync_code_refs(submission_id TEXT PRIMARY KEY,reference TEXT);'
                      'CREATE TABLE submissions(id TEXT PRIMARY KEY,code TEXT);')
    service = SimpleNamespace(lock=CountingLock(), connection=db,
        _now=lambda: dt.datetime(2026, 11, 9, 12, 0, tzinfo=dt.timezone.utc))
    result.sync = SimpleNamespace(service=service)
    result.enabled = True
    result.repair_needed = False
    result.graph = {}
    def store(identity, kind, payload, children, uploaded=0):
        assert not service.lock.held, 'graph callback held the personal database lock'
        result.graph[identity] = dict(kind=kind, payload=payload,
            children=json.dumps(children), uploaded_at=uploaded)
    result._store = store
    result._cached = lambda identity: result.graph.get(identity)
    def request(*_args, **_kwargs):
        raise AssertionError('the pure graph oracle must not request HTTP')
    result.request = request
    return result


def wire(graph):
    return [dict(hash=identity, kind=item['kind'],
        data=base64.b64encode(item['payload']).decode('ascii'), children=json.loads(item['children']))
        for identity, item in sorted(graph.items())]


def source_state():
    state = dict(format='tb-account-state-v1', tables={},
        publicAccounts={'codeforces': {'handle': 'synthetic-only', 'rating': 1e-5,
            'label': '\u4e2d\u6587\U0001f600\u2028', 'enabled': True, 'zero': -0.0}})
    for table, keys in TABLES.items():
        state['tables'][table] = [{**{key: f'{table}:{key}:\u539f\u6837' for key in keys},
            'data': '{"synthetic":true}', 'kept_unknown_column': '\\n\t\u4e2d\u6587'}]
    for table in ('tb_rank_profile', 'official_xp_state'):
        state['tables'][table][0]['id'] = 1
    state['tables']['drafts'][0]['context'] = ''
    state['tables']['training'] += [{'id': 'z', 'data': 'last'}, {'id': 'a', 'data': 'first'}]
    submissions = [
        dict(id='cold', code='// \u516c\u5f00\u6784\u9020\u5939\u5177\nint main(){}\n', finished_at='2026-10-10T11:59:59Z'),
        dict(id='exact', code='exact boundary stays inline', finished_at='2026-10-10T12:00:00Z'),
        dict(id='warm', code='warm', finished_at='2026-11-09T12:00:00Z'),
        dict(id='naive', code='naive UTC', finished_at='2026-10-10T11:59:59'),
        dict(id='offset', code='offset UTC', finished_at='2026-10-10T13:59:59+02:00'),
        dict(id='date', code='date only', finished_at='2026-10-09'),
        dict(id='invalid', code='invalid date stays inline', finished_at='not-a-date'),
        dict(id='empty', code='', finished_at='2020-01-01'),
    ]
    # Same real bucket, different file offsets. Intentionally unsorted source order.
    bucket = hashlib.sha256(b'group-0').hexdigest()[0]
    ids = [f'group-{i}' for i in range(300) if hashlib.sha256(f'group-{i}'.encode()).hexdigest()[0] == bucket][:4]
    submissions += [dict(id=identity, code=('// file ' + identity + '\n') * 1500,
        finished_at='2020-01-01') for identity in reversed(ids)]
    submissions += [dict(id='large', code='/*synthetic*/' * 6000, finished_at='2020-01-01')]
    for row in submissions:
        row['submitted_at'] = '2026-09-03T01:00:00Z'
        row['status'] = 'WA'
    state['tables']['submissions'] = submissions
    return state


def export(path):
    native = transport()
    state = source_state()
    canonical = native.canonicalize(state)
    packed = native.pack(canonical)
    # Keep an old-style 3-field reference as an independent compatibility case.
    legacy_code = '// synthetic legacy\n\u4e2d\u6587\U0001f600\n'.encode()
    legacy_root = native.write_blob(legacy_code)
    legacy_ref = chunks.CODE_PREFIX + chunks.encode(dict(root=legacy_root,
        sha256=hashlib.sha256(legacy_code).hexdigest(), bytes=len(legacy_code))).decode()
    floats = [0.0, -0.0, 1e-5, 1e-4, 1e15, 1e16, 1.2345678901234567e30,
        sys.float_info.max, sys.float_info.min, float.fromhex('0x0.0000000000001p-1022')]
    rng = random.Random(20261109)
    for _ in range(4096):
        value = struct.unpack('!d', rng.getrandbits(64).to_bytes(8, 'big'))[0]
        if math.isfinite(value): floats.append(value)
    vectors = [dict(bits=str(int.from_bytes(struct.pack('!d', value), 'big')),
        json=chunks.encode(value).decode()) for value in floats]
    payload = dict(state=state, canonical=canonical, root=packed,
        objects=wire(native.graph), legacyReference=legacy_ref,
        legacyCode=legacy_code.decode(), floatVectors=vectors,
        sources={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            for name in ('backend/account_chunks.py','backend/account_sync.py')},
        graphCallbacksHeldLock=False, httpRequests=0)
    Path(path).write_bytes(chunks.encode(payload))


def verify(path):
    value = json.loads(Path(path).read_bytes())
    native = transport()
    for item in value['objects']:
        payload = base64.b64decode(item['data'], validate=True)
        assert chunks.object_hash(item['kind'], payload, item['children']) == item['hash']
        native._store(item['hash'], item['kind'], payload, item['children'])
    native.answer = {'root': value['root']}
    native.canonicalize = lambda state: state  # isolate the actual old manifest reader
    unpacked = native.get()['state']
    assert unpacked == value['unpacked'], 'Python manifest reader differs from Rust'
    codes = 0
    for item in value['codes']:
        native.sync.service.connection.execute('INSERT INTO submissions VALUES(?,?)', (item['id'], ''))
        native.sync.service.connection.execute('INSERT INTO account_sync_code_refs VALUES(?,?)', (item['id'], item['reference']))
        actual = native.submission_code(item['id'])
        assert actual == item['code']
        assert native.sync.service.connection.execute('SELECT code FROM submissions WHERE id=?', (item['id'],)).fetchone()[0] == item['code']
        codes += 1
    print(json.dumps(dict(pythonReadRustManifest=True, pythonReadRustCodes=codes,
        objects=len(native.graph), httpRequests=0, graphCallbacksHeldLock=False)))


if __name__ == '__main__':
    {'export': export, 'verify': verify}[sys.argv[1]](sys.argv[2])
