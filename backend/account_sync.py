"""Account-owned learning state, synchronized without credentials or network locks.

SQLite remains the durable local journal. The shared account database stores the
canonical version; a successful login downloads it before exposing a workspace.
"""
from __future__ import annotations

import copy
import base64
import datetime as dt
import gzip
import hashlib
import io
import json
import re
import threading
import time

from training import ServiceError


TABLES = {
    'training': ('id',), 'practice_sets': ('id',), 'contests': ('id',),
    'drafts': ('problem_id', 'context'), 'submissions': ('id',),
    'tb_rank_profile': ('id',), 'official_first_xp_awards': ('problem_key',),
    'official_xp_state': ('id',), 'daily_missions': ('day', 'id'),
    'goals': ('id',), 'goal_daily_assignments': ('goal_id', 'day'),
    'ranking_receipts': ('endpoint', 'event_id'),
    'ranking_reward_totals': ('endpoint', 'user_id'),
    'achievement_xp_claims': ('achievement_id',),
    'account_preferences': ('key',),
    'account_problem_facts': ('problem_id',),
    'account_sync_conflicts': ('id',),
}
PROFILE_KEYS = ('platform', 'handle', 'displayName', 'url', 'status', 'rating',
                'maxRating', 'rank', 'solvedCount', 'submissionCount',
                'updatedAt', 'error', 'history', 'solved', 'activity')
EVIDENCE_KEYS = {'solved': ('key', 'url', 'title', 'tags', 'difficulty', 'acceptedAt'),
                 'history': ('date', 'rating', 'contest', 'rank'),
                 'activity': ('date', 'submissions', 'accepted')}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True)


def snapshot_payload(state):
    """Compress incrementally instead of retaining another full private journal."""
    buffer=io.BytesIO();checksum=hashlib.sha256();size=0
    encoder=json.JSONEncoder(ensure_ascii=False,separators=(',',':'),sort_keys=True)
    with gzip.GzipFile(fileobj=buffer,mode='wb',compresslevel=6,mtime=0) as stream:
        for text in encoder.iterencode(state):
            part=text.encode('utf-8');size+=len(part)
            if size>64*1024*1024:
                raise ServiceError(413,'账号学习记录超过同步容量，本机记录已保留，请先联系维护者扩容')
            checksum.update(part);stream.write(part)
    payload=base64.b64encode(buffer.getvalue()).decode('ascii')
    if len(payload)>4*1024*1024-2048:
        raise ServiceError(413,'账号学习记录超过同步容量，本机记录已保留，请先联系维护者扩容')
    return {'format':'tb-account-state-gzip-v1','payload':payload,'sha256':checksum.hexdigest(),'uncompressedBytes':size}


def digest(value):
    return hashlib.sha256(encoded(value).encode('utf-8')).hexdigest()


def baselines(state):
    return {'tables': {table: {encoded([row.get(key) for key in keys]): digest(row)
                              for row in state['tables'].get(table, [])}
                       for table, keys in TABLES.items()},
            'publicAccounts': {platform: digest(profile) for platform, profile in state['publicAccounts'].items()}}


def clean_profile(value):
    result = {key: copy.deepcopy(value[key]) for key in PROFILE_KEYS if key in value}
    for key, allowed in EVIDENCE_KEYS.items():
        result[key] = [{name: copy.deepcopy(row[name]) for name in allowed if name in row}
                       for row in result.get(key, []) if isinstance(row, dict)]
    return result


def merge_states(remote, local, baseline=None):
    """One-time legacy merge. Never sum XP or turn samples into official AC.

    Conflicting versions remain in an account-owned recovery table, including
    the losing draft. Already synchronized clients replace from the authority
    instead, so normal deletes are not resurrected on the next login.
    """
    if remote is None:
        return copy.deepcopy(local)
    result = copy.deepcopy(remote)
    baseline = baseline or {}
    conflicts = {row['id']: row for row in result['tables'].get('account_sync_conflicts', [])}

    def preserve(table, row):
        value = {'table': table, 'row': row}
        key = digest(value)
        conflicts[key] = {'id': key, 'data': encoded(value)}

    for table, keys in TABLES.items():
        if table == 'account_sync_conflicts':
            for row in local['tables'].get(table, []):
                conflicts[row['id']] = row
            continue
        rows = {tuple(row.get(key) for key in keys): copy.deepcopy(row)
                for row in result['tables'].get(table, [])}
        previous_rows = baseline.get('tables', {}).get(table, {})
        local_keys = {encoded([row.get(key) for key in keys]) for row in local['tables'].get(table, [])}
        for key, old in list(rows.items()):
            previous = previous_rows.get(encoded(list(key)))
            if previous and encoded(list(key)) not in local_keys:
                if digest(old) == previous:
                    del rows[key]  # An actual pending local deletion.
                else:
                    preserve(table, {'_deleted': True, 'key': list(key)})
        for row in local['tables'].get(table, []):
            key = tuple(row.get(name) for name in keys)
            old = rows.get(key)
            previous = previous_rows.get(encoded(list(key)))
            if old is None:
                if previous is None or digest(row) != previous:
                    rows[key] = copy.deepcopy(row)
                continue
            if old == row:
                continue
            timestamp_fields = {
                'training': ('removed_at', 'active_at', 'last_local_at', 'last_review_at'),
                'drafts': ('saved_at',), 'submissions': ('finished_at', 'submitted_at'),
                'contests': ('deleted_at', 'finished_at', 'started_at'),
                'ranking_reward_totals': ('updated_at',),
                'account_preferences': ('updated_at',),
                'account_problem_facts': ('updated_at',),
            }.get(table, ())
            stamp = lambda record: max((str(record.get(field) or '') for field in timestamp_fields), default='')
            if previous and digest(row) == previous:
                winner = copy.deepcopy(old)
            elif previous and digest(old) == previous:
                winner = copy.deepcopy(row)
            else:
                winner = copy.deepcopy(row if stamp(row) > stamp(old) else old)
            preserve(table, old if winner == row else row)
            if table == 'official_first_xp_awards':
                winner['awarded_xp'] = max(old['awarded_xp'], row['awarded_xp'])
                winner['accepted_at'] = min(old['accepted_at'], row['accepted_at'])
            elif table in ('tb_rank_profile', 'official_xp_state'):
                name = 'unlocked_at' if table == 'tb_rank_profile' else 'migrated_at'
                winner[name] = min(old[name], row[name])
            elif table == 'daily_missions':
                winner['awarded_xp'] = max(old['awarded_xp'], row['awarded_xp'])
                claims = [item for item in (old.get('claimed_at'), row.get('claimed_at')) if item]
                winner['claimed_at'] = min(claims) if claims else None
            elif table == 'achievement_xp_claims':
                winner['awarded_xp'] = max(old['awarded_xp'], row['awarded_xp'])
                unlocks = [item for item in (old['unlocked_at'], row['unlocked_at']) if item]
                winner['unlocked_at'] = min(unlocks) if unlocks else None
                winner['claimed_at'] = min(old['claimed_at'], row['claimed_at'])
            elif table == 'ranking_reward_totals':
                winner['total_xp'] = max(old['total_xp'], row['total_xp'])
            elif table == 'account_preferences' and winner.get('key') == 'ui':
                from preferences import merge_seen_achievements
                try:
                    left, right = json.loads(old['value']), json.loads(row['value'])
                except (ValueError, TypeError):
                    left = right = None  # Preserve malformed legacy documents in conflicts without blocking the rest of a login.
                if isinstance(left, dict) and isinstance(right, dict):
                    preferences = json.loads(winner['value'])
                    if 'seenAchievements' in left or 'seenAchievements' in right:
                        preferences['seenAchievements'] = merge_seen_achievements(left.get('seenAchievements'), right.get('seenAchievements'))
                    if left.get('onboardingCompleted') is True or right.get('onboardingCompleted') is True:
                        preferences['onboardingCompleted'] = True
                    winner['value'] = encoded(preferences)
            rows[key] = winner
        result['tables'][table] = list(rows.values())
    # Independent old workspaces can each contain a running mock contest. Keep
    # both histories, choosing only the most recently started one as running.
    running = sorted((row for row in result['tables'].get('contests', []) if row['status'] == 'running'),
                     key=lambda row: (row['started_at'], row['id']), reverse=True)
    for row in running[1:]:
        preserve('contests', copy.deepcopy(row))
        row['status'], row['finished_at'] = 'finished', row['deadline']
    names = set()
    for row in sorted(result['tables'].get('practice_sets', []), key=lambda row: row['id']):
        if row['name'] in names:
            preserve('practice_sets', copy.deepcopy(row))
            row['name'] += ' (' + row['id'][:8] + ')'
        names.add(row['name'])
    for platform, profile in local.get('publicAccounts', {}).items():
        old = result['publicAccounts'].get(platform)
        previous = baseline.get('publicAccounts', {}).get(platform)
        if old is None or (previous and digest(profile) != previous and digest(old) == previous) or (
                not previous and old.get('handle') == profile.get('handle') and (profile.get('updatedAt') or '') > (old.get('updatedAt') or '')):
            if old is not None and old != profile:
                preserve('publicAccounts', old)
            result['publicAccounts'][platform] = copy.deepcopy(profile)
        elif old != profile:
            preserve('publicAccounts', profile)
    result['tables']['account_sync_conflicts'] = list(conflicts.values())
    for table, keys in TABLES.items():
        result['tables'][table].sort(key=lambda row: tuple(str(row.get(key) or '') for key in keys))
    return result


class AccountStateSync:
    def __init__(self, accounts, service, session):
        self.accounts, self.service, self.session = accounts, service, session
        self.owner = session['userId']
        self.operation = threading.RLock()
        self.status_lock = threading.RLock()
        self.wake, self.stop = threading.Event(), threading.Event()
        self.thread = None
        self.heartbeat_thread = None
        self.revision = 0
        self.synced_hash = ''
        self.last_changes = -1
        self.last_profile_hash = ''
        self.last_profile_stamp = None
        self.captured_profile_stamp = None
        self.last_facts_signature = None
        self.facts_ids = None
        self.status, self.error, self.last_synced = 'syncing', '', None
        self.pending = True
        with service.lock:
            service.connection.executescript('''
              CREATE TABLE IF NOT EXISTS account_sync_meta (id INTEGER PRIMARY KEY CHECK(id=1),value TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS account_sync_conflicts (id TEXT PRIMARY KEY,data TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS achievement_xp_claims (
                achievement_id TEXT PRIMARY KEY,unlocked_at TEXT,
                awarded_xp INTEGER NOT NULL,claimed_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS account_preferences (
                key TEXT PRIMARY KEY,value TEXT NOT NULL,updated_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS account_problem_facts (
                problem_id TEXT PRIMARY KEY,value TEXT NOT NULL,updated_at TEXT NOT NULL);
            ''')
            row = service.connection.execute('SELECT value FROM account_sync_meta WHERE id=1').fetchone()
            self.meta = json.loads(row[0]) if row else {}
        if self.meta and (self.meta.get('owner') != self.owner or self.meta.get('endpoint') != session['endpoint']):
            raise ServiceError(409, '个人工作区所属账号不一致，请保留本地数据并检查账号设置')
        from account_chunks import ChunkTransport
        self.chunks=ChunkTransport(self)

    def _call(self,method,path,body=None,cached_revision=None):
        if path=='/v1/accounts/state' and self.chunks.enabled:
            return self.chunks.get(cached_revision) if method=='GET' else self.chunks.put(body)
        return self._legacy_call(method,path,body,cached_revision)

    def _legacy_call(self, method, path, body=None, cached_revision=None):
        timeout = 20
        if method == 'PUT' and path == '/v1/accounts/state':
            # HTTPS sendall applies its timeout to the entire compressed upload.
            # A valid multi-megabyte journal can take longer than 20 seconds on
            # a slow uplink. Keep ordinary reads/heartbeats on their short limit.
            timeout = 150
            body = {'revision':body['revision'],'state':snapshot_payload(body['state'])}
        session = self.session
        options = {'state_revision': cached_revision} if cached_revision is not None else {}
        try:
            value = self.accounts._remote(method, path, body, session, invalidate=False,
                                          maximum=4 * 1024 * 1024, timeout=timeout, **options)
        except ServiceError as issue:
            # Password changes rotate the token while a heartbeat can be in
            # flight. A late rejection of that old token must not log out the
            # replacement session. Its rejected request is safe to retry once.
            if issue.status == 401 and session['token'] != self.session['token']:
                value = self.accounts._remote(method, path, body, self.session, invalidate=False,
                                               maximum=4 * 1024 * 1024, timeout=timeout, **options)
            else:
                raise
        if path == '/v1/accounts/state' and isinstance(value.get('state'), dict) and value['state'].get('format') == 'tb-account-state-gzip-v1':
            try:
                compressed = value['state']
                with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(compressed['payload'], validate=True))) as stream:
                    raw = stream.read(64 * 1024 * 1024 + 1)
                if (len(raw) > 64 * 1024 * 1024 or len(raw) != compressed['uncompressedBytes'] or
                        hashlib.sha256(raw).hexdigest() != compressed['sha256']):
                    raise ValueError('Invalid state checksum')
                state = json.loads(raw)
                if (not isinstance(state, dict) or state.get('format') != 'tb-account-state-v1' or
                        not isinstance(state.get('tables'), dict) or set(state['tables']) - set(TABLES) or
                        not isinstance(state.get('publicAccounts'), dict)):
                    raise ValueError('Invalid state schema')
                value['state'] = state
            except (ValueError, OSError, EOFError, KeyError, TypeError):
                raise ServiceError(503, '云端账号数据校验失败，本机记录已保留，请稍后重试') from None
        return value

    def _profiles(self, import_original=False):
        current = self.accounts.session
        use_global = current and current['userId'] == self.owner and self.accounts.server.training is self.service
        extensions = getattr(self.accounts.server.store, 'extensions', None)
        if extensions is not None and (use_global or import_original):
            with extensions.lock:
                self.captured_profile_stamp = self._profile_stamp_locked(extensions)
                profiles = {}
                for platform in ('codeforces', 'atcoder'):
                    handle = extensions.state['settings']['accounts'].get(platform, '')
                    from public_platforms import profile
                    value = extensions.state['accounts'].get(platform) or profile(platform, handle)
                    if value.get('handle') != handle:
                        value = profile(platform, handle)
                    profiles[platform] = clean_profile(value)
                return profiles
        self.captured_profile_stamp = None
        return copy.deepcopy(self.meta.get('publicAccounts', {}))

    @staticmethod
    def _profile_stamp_locked(extensions):
        # Public providers replace profiles atomically. Inspect their identity
        # and small revision fields instead of copying thousands of solved
        # records on every 750 ms heartbeat tick.
        values = []
        for platform in ('codeforces', 'atcoder'):
            original = extensions.state['accounts'].get(platform)
            value = original or {}
            values.append((extensions.state['settings']['accounts'].get(platform, ''), id(original),
                           value.get('updatedAt'), value.get('rating'), value.get('maxRating'),
                           value.get('solvedCount'), value.get('submissionCount'),
                           value.get('status'), len(value.get('solved', [])),
                           len(value.get('history', [])), len(value.get('activity', []))))
        return tuple(values)

    def _profile_stamp(self):
        extensions = getattr(self.accounts.server.store, 'extensions', None)
        if extensions is None:
            return None
        with extensions.lock:
            return self._profile_stamp_locked(extensions)

    def _capture(self, import_original=False, refresh_facts=True):
        if refresh_facts:
            self._refresh_problem_facts()
        # Public profile evidence is copied under its own short lock. No network
        # call occurs under either the integration lock or the SQLite lock.
        profiles = self._profiles(import_original)
        with self.service.lock:
            tables = {name: [dict(row) for row in self.service.connection.execute(f'SELECT * FROM "{name}" ORDER BY ' + ','.join(keys))]
                      for name, keys in TABLES.items()}
            changes = self.service.connection.total_changes
        state=self.chunks.canonicalize({'format':'tb-account-state-v1','tables':tables,'publicAccounts':profiles})
        with self.service.lock:changes=self.service.connection.total_changes
        return state,changes

    def _facts_signature(self):
        library = getattr(self.service.store, 'library', None)
        signature = library.content_signature() if library is not None else None
        extensions = getattr(self.service.store, 'extensions', None)
        if extensions is not None:
            with extensions.lock:
                public = (extensions.state.get('sync', {}).get('lastSuccessAt'),
                          extensions.state.get('sync', {}).get('busy'),
                          len(extensions.state.get('rows', {})), len(extensions.state.get('difficultyMetadata', {})))
        else:
            public = None
        return signature, public

    @staticmethod
    def _portable_json(value):
        forbidden = {'path', 'source_path', 'sourcePath', 'cachePath', 'localPath', 'password',
                     'auth_token', 'token', 'apiKey', 'api_key', 'secret', 'cookies', 'cookie', 'headers'}
        if isinstance(value, dict):
            return {key: AccountStateSync._portable_json(item) for key, item in value.items()
                    if key not in forbidden and not re.match(r'^(?:[A-Za-z]:[\\/]|\\\\)', str(key))}
        if isinstance(value, list):
            return [AccountStateSync._portable_json(item) for item in value]
        if isinstance(value, str) and re.match(r'^(?:[A-Za-z]:[\\/]|\\\\)', value):
            return ''
        return value

    @staticmethod
    def _portable_content(value):
        if not value:
            return None
        value = copy.deepcopy(value)
        # Imported illustrations can use absolute original references. Give
        # embedded bytes a portable name instead of sending a machine path.
        images = {}
        for name, data in value.get('images', {}).items():
            target = name
            if re.match(r'^(?:[A-Za-z]:[\\/]|\\\\|/(?:home|Users|opt)/)', name):
                target = 'portable/' + hashlib.sha256(name.encode('utf-8')).hexdigest()
                value['markdown'] = (value.get('markdown') or '').replace(name, target)
            images[target] = data
        value['images'] = images
        return AccountStateSync._portable_json(value)

    def _refresh_problem_facts(self):
        signature = self._facts_signature()
        with self.service.lock:
            db = self.service.connection
            tracked = {row[0] for row in db.execute('''SELECT id FROM training
                UNION SELECT problem_id FROM drafts UNION SELECT problem_id FROM submissions''') if row[0]}
            for table, column in (('contests', 'slots'), ('practice_sets', 'ids'), ('goal_daily_assignments', 'ids')):
                for row in db.execute(f'SELECT {column} FROM {table}'):
                    try:
                        items = json.loads(row[0])
                        tracked.update(item.get('id') if isinstance(item, dict) else item for item in items
                                       if isinstance(item, str) or isinstance(item, dict) and isinstance(item.get('id'), str))
                    except (TypeError, ValueError):
                        continue
            for record in db.execute("SELECT value FROM account_preferences WHERE key LIKE 'custom-training-list:%'"):
                try:
                    value = json.loads(record[0])
                    if not value.get('deleted'):
                        tracked.update(item['problemId'] for item in value.get('problems', []) if isinstance(item.get('problemId'), str))
                except (ValueError, TypeError, AttributeError):
                    continue
            tracked = frozenset(tracked)
            if signature == self.last_facts_signature and tracked == self.facts_ids:
                return
            previous = {row['problem_id']: row['value'] for row in db.execute('SELECT problem_id,value FROM account_problem_facts')}
        store = self.service.store
        library = getattr(store, 'library', None)
        updates = []
        for identity in sorted(tracked):
            try:
                raw = store.row(identity)
                row = store.encode_row(raw)
            except Exception as issue:
                if getattr(issue, 'status', None) == 404:
                    continue  # A downloaded private fact remains the fallback.
                raise
            fact = {'row': self._portable_json(dict(row, id=identity)),
                    'raw': {key: copy.deepcopy(raw[key]) for key in ('场次', '题号', '题名', '知识点', '难度', '状态', '日期', '_remote', '_platform', '_series') if key in raw}}
            fact['raw'].update(_id=identity, _url=row.get('url'))
            old = json.loads(previous[identity]) if identity in previous else {}
            if library is not None:
                found = library.find(identity, row.get('url'))
                resolved = found['id'] if found else identity
                statement = library.statement(resolved)
                if statement:
                    fact['statement'] = self._portable_content(statement)
                elif old.get('statement'):
                    fact['statement'] = old['statement']
                if found:
                    with library.connection() as connection:
                        bundled = connection.execute("SELECT 1 FROM bundled_items WHERE table_name='problems' AND item_id=?", (resolved,)).fetchone()
                    if not bundled:
                        for key, variant in (('solution', 'default'), ('detailedSolution', 'detailed')):
                            content = library.solution(resolved, variant)
                            if content:
                                fact[key] = self._portable_content(content)
                            elif old.get(key):
                                fact[key] = old[key]
            value = encoded(self._portable_json(fact))
            if value != previous.get(identity):
                updates.append((identity, value, dt.datetime.now(dt.timezone.utc).isoformat()))
        if updates:
            with self.service.lock:
                self.service.connection.executemany('''INSERT INTO account_problem_facts VALUES(?,?,?)
                  ON CONFLICT(problem_id) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at''', updates)
        self.last_facts_signature, self.facts_ids = signature, tracked

    def _persist_meta(self, state, changes):
        self.meta = {'owner': self.owner, 'endpoint': self.session['endpoint'], 'revision': self.revision,
                     'syncedHash': digest(state), 'publicAccounts': state['publicAccounts'], 'lastSyncedAt': self.last_synced,
                     'baseline': baselines(state),'transport':2 if self.chunks.enabled else 1}
        metadata = encoded(self.meta)
        with self.service.lock:
            self.service.connection.execute('INSERT INTO account_sync_meta VALUES(1,?) ON CONFLICT(id) DO UPDATE SET value=excluded.value', (metadata,))
            # The metadata write is ours; no training mutation can slip between
            # reading the journal counter and saving its acknowledgement.
            self.last_changes = self.service.connection.total_changes if self.service.connection.total_changes == changes + 1 else changes
        self.synced_hash = self.meta['syncedHash']
        self.last_profile_hash = digest(state['publicAccounts'])
        self.last_profile_stamp = self.captured_profile_stamp

    def _apply(self, state):
        with self.service.lock:
            self.service._backup()
            db = self.service.connection
            db.execute('BEGIN IMMEDIATE')
            try:
                previous_codes=dict(db.execute('SELECT id,code FROM submissions'))
                for table in TABLES:
                    rows = state['tables'].get(table, [])
                    allowed = {row[1] for row in db.execute(f'PRAGMA table_info("{table}")')}
                    db.execute(f'DELETE FROM "{table}"')
                    for row in rows:
                        if table=='submissions':row=self.chunks.apply_code(row,previous_codes)
                        names = [name for name in row if name in allowed]
                        db.execute(f'INSERT INTO "{table}" (' + ','.join('"' + name + '"' for name in names) + ') VALUES(' + ','.join('?' for _ in names) + ')', [row[name] for name in names])
                db.execute('COMMIT')
            except BaseException:
                db.execute('ROLLBACK')
                raise
            changes = db.total_changes
        self._apply_profiles(state)
        return changes

    def _apply_profiles(self, state):
        extensions = getattr(self.accounts.server.store, 'extensions', None)
        if extensions is not None:
            from public_platforms import profile
            with extensions.lock:
                for platform in ('codeforces', 'atcoder'):
                    value = state['publicAccounts'].get(platform) or profile(platform, '')
                    extensions.state['settings']['accounts'][platform] = value['handle']
                    extensions.state['accounts'][platform] = copy.deepcopy(value)
                # The v1 shared service only accepts CF/AtCoder public profiles.
                # Receipt-only numeric IDs use its existing private journal and
                # must also clear on an account without bindings.
                from preferences import receipt_bindings
                for platform, handle in receipt_bindings(state['tables'].get('account_preferences', [])).items():
                    extensions.state['settings']['accounts'][platform] = handle
                    extensions.state['accounts'][platform] = profile(platform, handle)
                extensions._save()

    def initialize(self):
        with self.operation:
            self.chunks.negotiate()
            imported = (self.accounts.registry.get('activeOwner') == self.owner or
                        not self.meta and self.accounts.registry.get('originalOwner') == self.owner)
            # Cached portable facts are already durable. Refresh their public
            # metadata in the background after authentication, not on the
            # startup critical path. First migrations still capture everything.
            local, local_changes = self._capture(import_original=imported, refresh_facts=not bool(self.meta))
            local_matches = bool(self.meta and digest(local) == self.meta.get('syncedHash'))
            # A matching remote revision authenticates the saved credential and
            # proves the last applied snapshot is still current. Pending local
            # edits need an upload, not another download of that same snapshot.
            cached_revision = self.meta.get('revision') if self.meta and self.meta.get('syncedHash') else None
            if type(cached_revision) is not int or cached_revision <= 0:
                cached_revision = None
            upload_pending = False
            try:
                answer = self._call('GET', '/v1/accounts/state', cached_revision=cached_revision)
            except ServiceError as issue:
                if issue.status == 404:
                    raise ServiceError(503, '账号云端同步服务正在升级，请稍后重试；本机数据已保留') from None
                raise
            if answer.get('unchanged') is True:
                if cached_revision is None or answer.get('revision') != cached_revision:
                    raise ServiceError(503, '云端同步版本不一致，请重试；本机数据已保留')
                upload_pending = not local_matches
                answer = {'revision': cached_revision, 'state': local}
            if type(answer.get('revision')) is not int or 'state' not in answer:
                raise ServiceError(503, '账号同步服务需要升级，请稍后重试')
            self.revision = answer['revision']
            if answer['state'] is not None and local_matches:
                state = answer['state']
            else:
                state = merge_states(answer['state'], local, self.meta.get('baseline'))
            # Complete the first upload before exposing authentication. A failure
            # leaves the local workspace and session gate untouched.
            if upload_pending or answer['state'] != state or self.chunks.migrate:
                saved = self._call('PUT', '/v1/accounts/state', {'revision': self.revision, 'state': state})
                self.revision = saved['revision']
                self.last_synced = saved['savedAt']
            else:
                self.last_synced = dt.datetime.now(dt.timezone.utc).isoformat()
            # Most restarts restore the very same state. Do not take another
            # online backup and DELETE/INSERT every personal row in that case.
            if state != local:
                changes = self._apply(state)
            else:
                changes = local_changes
                self._apply_profiles(state)
            self._persist_meta(state, changes)
            with self.status_lock:
                self.status, self.error, self.pending = 'ready', '', False

    def snapshot(self):
        with self.status_lock:
            return {'status': self.status, 'error': self.error, 'pending': self.pending,
                    'lastSyncedAt': self.last_synced, 'revision': self.revision}

    def mark_pending(self):
        with self.service.lock:
            changed = self.service.connection.total_changes != self.last_changes
        if not changed and self._profile_stamp() == self.last_profile_stamp and self._facts_signature() == self.last_facts_signature:
            return self.snapshot()
        with self.status_lock:
            self.pending = True
        self.wake.set()
        return self.snapshot()

    def notify_write(self):
        # A completed API write already committed its SQLite transaction. Do
        # not re-enter training/catalog locks before sending its response.
        with self.status_lock:
            self.pending = True
        self.wake.set()

    def flush(self, wait=True):
        if not wait:
            return self.mark_pending()
        try:
            with self.operation:
                if self.stop.is_set():
                    return self.snapshot()
                state, changes = self._capture()
                signature = digest(state)
                if signature != self.synced_hash:
                    with self.status_lock:
                        self.status, self.pending = 'syncing', True
                    answer = self._call('PUT', '/v1/accounts/state', {'revision': self.revision, 'state': state})
                    self.revision, self.last_synced = answer['revision'], answer['savedAt']
                    self._persist_meta(state, changes)
                else:
                    with self.service.lock:
                        self.last_changes = changes
                    self.last_profile_stamp = self.captured_profile_stamp
                with self.service.lock:
                    still_dirty = self.service.connection.total_changes != self.last_changes
                still_dirty = still_dirty or self._profile_stamp() != self.last_profile_stamp
                with self.status_lock:
                    self.status, self.error, self.pending = 'ready', '', still_dirty
            return self.snapshot()
        except ServiceError as issue:
            with self.status_lock:
                self.status, self.error, self.pending = 'error', issue.message, True
            if issue.status == 401:
                self.accounts.invalidate(self.session['token'])
            raise

    def _loop(self):
        retry_at, next_flush = 0, 0
        while not self.stop.is_set():
            self.wake.wait(.75)
            self.wake.clear()
            if self.stop.is_set():
                break
            try:
                now = time.monotonic()
                with self.service.lock:
                    changed = self.service.connection.total_changes != self.last_changes
                profile_changed = self._profile_stamp() != self.last_profile_stamp
                facts_changed = self._facts_signature() != self.last_facts_signature
                if (changed or profile_changed or facts_changed or self.pending) and now >= max(retry_at, next_flush):
                    next_flush = now + .75
                    self.flush()
            except ServiceError as issue:
                with self.status_lock:
                    self.status, self.error = 'error', issue.message
                if issue.status == 401:
                    self.accounts.invalidate(self.session['token'])
                    break
                retry_at = time.monotonic() + 5
            except (OSError, ValueError):
                with self.status_lock:
                    self.status, self.error, self.pending = 'error', '同步暂时失败，本机数据已保留，后台将重试', True
                retry_at = time.monotonic() + 5

    def _heartbeat(self):
        # A slow upload must not postpone takeover detection. This thread only
        # reads a tiny session response and never exports or locks training data.
        while not self.stop.is_set():
            try:
                value = self._call('GET', '/v1/accounts/me')
                if value.get('account', {}).get('userId') != self.owner:
                    raise ServiceError(503, '账号响应不一致')
                with self.status_lock:
                    if self.status == 'error' and not self.pending:
                        self.status, self.error = 'ready', ''
            except ServiceError as issue:
                with self.status_lock:
                    self.status, self.error = 'error', issue.message
                if issue.status == 401:
                    self.accounts.invalidate(self.session['token'])
                    return
            if self.stop.wait(3):
                return

    def start(self):
        if self.thread is None:
            self.thread = threading.Thread(target=self._loop, name='tb-account-sync', daemon=True)
            self.thread.start()
            self.heartbeat_thread = threading.Thread(target=self._heartbeat, name='tb-account-session', daemon=True)
            self.heartbeat_thread.start()

    def close(self):
        self.stop.set()
        self.wake.set()
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(22)
        if self.heartbeat_thread and self.heartbeat_thread is not threading.current_thread():
            self.heartbeat_thread.join(22)
