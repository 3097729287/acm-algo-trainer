"""Submission-derived personal training, isolated from the read-only TB archive."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from contextvars import ContextVar
import datetime as dt
import hashlib
import inspect
import json
import logging
from pathlib import Path
import secrets
import sqlite3
import threading
import time
import uuid

UTC = dt.timezone.utc
TRAINING_ZONE = dt.timezone(dt.timedelta(hours=8))
FAILURES = {"WA", "TLE", "MLE", "RE", "CE", "OLE", "ERROR"}
VERDICTS = FAILURES | {"AC", "SAMPLE_PASS", "RUN_OK", "QUEUED", "RUNNING"}
MAX_CODE = 65_536
_LIBRARY_VIEW = ContextVar('tb_request_library', default=None)


class ServiceError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message
        super().__init__(message)


def iso(value):
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def parse_time(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


class TrainingService:
    def __init__(self, store, db_path, assets=None, judge=None, clock=None, backup_dir=None, rng=None, account_provider=None, admin_mode=False):
        self.admin_mode = bool(admin_mode)
        self.store = store
        self.account_provider = account_provider
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.clock = clock or (lambda: dt.datetime.now(UTC))
        self.rng = rng or secrets.SystemRandom()
        self._last_backup_at = None
        # A full directory mirrored into the backup name doubles its length.
        # Per-account paths then exceed SQLite's Windows path limit. Existing
        # backup folders stay intact; new backups use a stable short namespace.
        mirror = 'personal-' + hashlib.sha256(str(self.db_path.parent).encode('utf-8')).hexdigest()[:16]
        self.backup_dir = Path(backup_dir) if backup_dir else Path(__import__("toolutil").BACKUP_ROOT) / mirror
        existed = self.db_path.exists()
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA busy_timeout=5000")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        if existed:
            self._backup()
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS training (
              id TEXT PRIMARY KEY, active_at TEXT NOT NULL, solution_pending INTEGER NOT NULL DEFAULT 0,
              rewrite_due INTEGER NOT NULL DEFAULT 0, accepted_at TEXT, last_local_at TEXT,
              last_review_at TEXT, review_count INTEGER NOT NULL DEFAULT 0, mock_due INTEGER NOT NULL DEFAULT 0,
              solution_seen_at TEXT, mock_due_at TEXT, mock_due_context TEXT);
            CREATE TABLE IF NOT EXISTS practice_sets (
              id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, ids TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS contests (
              id TEXT PRIMARY KEY, name TEXT NOT NULL, status TEXT NOT NULL, started_at TEXT NOT NULL,
              deadline TEXT NOT NULL, finished_at TEXT, duration INTEGER NOT NULL, slots TEXT NOT NULL);
            CREATE UNIQUE INDEX IF NOT EXISTS one_running_contest ON contests(status) WHERE status='running';
            CREATE TABLE IF NOT EXISTS drafts (
              problem_id TEXT NOT NULL, context TEXT NOT NULL, code TEXT NOT NULL, saved_at TEXT NOT NULL,
              PRIMARY KEY(problem_id,context));
            CREATE TABLE IF NOT EXISTS submissions (
              id TEXT PRIMARY KEY, problem_id TEXT NOT NULL, contest_id TEXT, mode TEXT NOT NULL,
              code TEXT NOT NULL, submitted_at TEXT NOT NULL, finished_at TEXT, verdict TEXT NOT NULL,
              scope TEXT NOT NULL, time_ms REAL, memory_kb REAL, passed INTEGER NOT NULL DEFAULT 0,
              total INTEGER NOT NULL DEFAULT 0, output TEXT NOT NULL DEFAULT '', stderr TEXT NOT NULL DEFAULT '',
              message TEXT NOT NULL DEFAULT '', custom_input TEXT NOT NULL DEFAULT '', solution_seen INTEGER NOT NULL DEFAULT 0);
            CREATE INDEX IF NOT EXISTS submission_problem ON submissions(problem_id,submitted_at);
            CREATE INDEX IF NOT EXISTS submission_contest ON submissions(contest_id,submitted_at);
        """)
        for table, additions in (("training", {"solution_seen_at": "TEXT", "mock_due_at": "TEXT", "mock_due_context": "TEXT", "active": "INTEGER NOT NULL DEFAULT 1", "removed_at": "TEXT"}), ("submissions", {"solution_seen": "INTEGER NOT NULL DEFAULT 0", "sample_run": "INTEGER NOT NULL DEFAULT 0", "case_results": "TEXT NOT NULL DEFAULT '[]'"}), ("contests", {"config": "TEXT NOT NULL DEFAULT '{}'", "deleted_at": "TEXT"})):
            columns = {record[1] for record in self.connection.execute(f"PRAGMA table_info({table})")}
            for column, definition in additions.items():
                if column not in columns:
                    self.connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS tb_rank_profile (
              id INTEGER PRIMARY KEY CHECK(id=1), unlocked_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS official_first_xp_awards (
              problem_key TEXT PRIMARY KEY, accepted_at TEXT NOT NULL,
              awarded_xp INTEGER NOT NULL CHECK(awarded_xp >= 0));
            CREATE TABLE IF NOT EXISTS official_xp_state (
              id INTEGER PRIMARY KEY CHECK(id=1), migrated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS achievement_xp_claims (
              achievement_id TEXT PRIMARY KEY, unlocked_at TEXT,
              awarded_xp INTEGER NOT NULL CHECK(awarded_xp>=0), claimed_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS account_preferences (
              key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS account_problem_facts (
              problem_id TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS daily_missions (
              day TEXT NOT NULL, id TEXT NOT NULL, definition TEXT NOT NULL,
              claimed_at TEXT, awarded_xp INTEGER NOT NULL DEFAULT 0, evidence TEXT NOT NULL DEFAULT '[]',
              PRIMARY KEY(day,id));
            CREATE TABLE IF NOT EXISTS goals (
              id TEXT PRIMARY KEY, created_at TEXT NOT NULL, config TEXT NOT NULL,
              archived INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS goal_daily_assignments (
              goal_id TEXT NOT NULL, day TEXT NOT NULL, ids TEXT NOT NULL, target INTEGER, PRIMARY KEY(goal_id,day));
            CREATE TABLE IF NOT EXISTS ranking_profile (
              singleton INTEGER PRIMARY KEY CHECK(singleton=1), user_id TEXT NOT NULL UNIQUE,
              nickname TEXT NOT NULL, auth_token TEXT NOT NULL, endpoint TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL, last_synced_at TEXT);
            CREATE TABLE IF NOT EXISTS ranking_receipts (
              endpoint TEXT NOT NULL, event_id TEXT NOT NULL, accepted_at TEXT NOT NULL,
              PRIMARY KEY(endpoint,event_id));
            CREATE TABLE IF NOT EXISTS ranking_reward_totals (
              endpoint TEXT NOT NULL,user_id TEXT NOT NULL,total_xp INTEGER NOT NULL,
              awards TEXT NOT NULL DEFAULT '[]',updated_at TEXT NOT NULL,
              PRIMARY KEY(endpoint,user_id));
            CREATE TABLE IF NOT EXISTS official_pending (
              id TEXT PRIMARY KEY, session_id TEXT NOT NULL, submission_id TEXT NOT NULL,
              problem_id TEXT, url TEXT, code TEXT, platform TEXT, accepted_at TEXT);
        """)
        if not existed:
            self.connection.execute('INSERT OR IGNORE INTO official_xp_state VALUES(1,?)', (iso(self._now()),))
        if 'target' not in {row[1] for row in self.connection.execute('PRAGMA table_info(goal_daily_assignments)')}:
            self.connection.execute('ALTER TABLE goal_daily_assignments ADD COLUMN target INTEGER')
        from leaderboard import default_endpoint
        from persistence import load_document,save_document
        upgrade_marker=self.db_path.parent/'leaderboard-default-migration.json'
        if not load_document(upgrade_marker,False):
            with self.connection:
                self.connection.execute("UPDATE ranking_profile SET endpoint=? WHERE endpoint=''",(default_endpoint(),))
            save_document(upgrade_marker,True)
        if not self.connection.execute("SELECT 1 FROM ranking_profile WHERE singleton=1").fetchone():
            from leaderboard import default_endpoint
            with self._write() as connection:
                connection.execute("INSERT INTO ranking_profile(singleton,user_id,nickname,auth_token,endpoint,created_at) VALUES(1,?,?,?,?,?)",
                                   (str(uuid.uuid4()), "练习者", secrets.token_urlsafe(32), default_endpoint(), iso(self._now())))
        self.assets = assets
        self.judge = judge
        # Upgraded databases may still cache acceptance derived from local AC.
        # Replay before any workspace response or leaderboard synchronization.
        cached = self.connection.execute("SELECT id FROM training WHERE accepted_at IS NOT NULL").fetchall()
        if cached:
            with self._library_view(), self._write() as connection:
                for record in cached:
                    self._recompute_progress(connection, record["id"])
        self.previews = {}
        self.previous_previews = {}
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="tb-judge")
        self.closed = False
        self.cancellations = {}
        from leaderboard import LeaderboardClient
        self.leaderboard = LeaderboardClient(self)
        self.leaderboard.queue_sync()
        self.jobs_started = account_provider is None
        if self.jobs_started:
            pending = self.connection.execute("SELECT id FROM submissions WHERE finished_at IS NULL").fetchall()
            for record in pending:
                self._enqueue(record["id"])

    def _now(self):
        value = self.clock()
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    def _backup(self):
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        destination = self.backup_dir / f"{self.db_path.name}.{timestamp}.{uuid.uuid4().hex[:6]}.bak"
        backup = sqlite3.connect(destination)
        try:
            self.connection.backup(backup)
        finally:
            backup.close()
        self._last_backup_at = time.monotonic()

    @contextmanager
    def _write(self):
        with self.lock:
            # SQLite commits remain fully durable. Full online recovery copies
            # are bounded, rather than copying the entire code history for
            # every autosave, mission update and receipt in the same minute.
            # Migrations and cloud replacements still call _backup explicitly.
            if self._last_backup_at is None or time.monotonic() - self._last_backup_at >= 300:
                self._backup()
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                yield self.connection
                self.connection.execute("COMMIT")
            except BaseException:
                self.connection.execute("ROLLBACK")
                raise

    def _library(self):
        snapshot = _LIBRARY_VIEW.get()
        if snapshot is not None and snapshot[0] is self:
            return list(snapshot[1])
        return self.store.data()["rows"]

    @contextmanager
    def _library_view(self):
        """Reuse one fresh catalog during this call, never across requests or threads."""
        snapshot = _LIBRARY_VIEW.get()
        token = None
        if snapshot is None or snapshot[0] is not self:
            token = _LIBRARY_VIEW.set((self, self._library(), {}))
        try:
            yield
        finally:
            if token is not None:
                _LIBRARY_VIEW.reset(token)

    def _row(self, identity):
        if not isinstance(identity, str) or not identity or len(identity) > 512:
            raise ServiceError(400, "题目编号无效")
        rows = [row for row in self._library() if row["id"] == identity]
        if not rows and hasattr(self.store, "row"):
            try:
                raw = self.store.row(identity)
                rows = [self.store.encode_row(raw, self._now().date())]
                rows[0]["id"] = identity
            except Exception as error:
                if getattr(error, "status", None) != 404:
                    raise
        if not rows:
            fact = self.portable_problem(identity)
            if fact and isinstance(fact.get('row'), dict):
                rows = [dict(fact['row'], id=identity)]
        if len(rows) != 1:
            raise ServiceError(404 if not rows else 409, "没有找到唯一对应的题目，请刷新")
        return rows[0]

    def portable_problem(self, identity):
        """Only this account's referenced imported/retired problem facts."""
        with self.lock:
            row = self.connection.execute('SELECT value FROM account_problem_facts WHERE problem_id=?', (identity,)).fetchone()
            return json.loads(row['value']) if row else None

    def portable_solution(self, identity):
        fact = self.portable_problem(identity)
        if not fact or not (fact.get('solution') or fact.get('detailedSolution')):
            return None
        value = dict(fact.get('solution') or {'markdown': '', 'images': {}, 'path': ''})
        value.update(title=fact.get('row', {}).get('title') or identity,
                     url=fact.get('row', {}).get('url'),
                     detailedSolution=fact.get('detailedSolution'))
        return value

    def _asset_library(self):
        with self.lock:
            if self.assets is None:
                from assets import AssetLibrary
                self.assets = AssetLibrary(self.store, portable=self.portable_problem)
            return self.assets

    def _judge(self):
        with self.lock:
            if self.judge is None:
                from judge import Judge
                self.judge = Judge(self._asset_library(), self.db_path.parent / "judge-work")
            return self.judge

    def _activate(self, connection, identity, timestamp):
        connection.execute("INSERT INTO training(id,active_at) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET active=1,removed_at=NULL,active_at=MAX(training.active_at,excluded.active_at)", (identity, timestamp))
        self._recompute_progress(connection, identity)

    def _identity_map(self, library=None):
        from insights import canonical_url
        snapshot = _LIBRARY_VIEW.get()
        scoped = snapshot[2] if snapshot is not None and snapshot[0] is self else None
        if scoped is not None and 'aliases' in scoped:
            return scoped['aliases']
        rows = list(library if library is not None else self._library())
        extensions = getattr(self.store, "extensions", None)
        if extensions is not None:
            identities = getattr(extensions, 'identity_rows', None)
            rows += identities() if callable(identities) else extensions.rows()
        known = {row["id"] for row in rows}
        if hasattr(self.store, "row"):
            for record in self.connection.execute("SELECT id FROM training"):
                if record["id"] not in known:
                    try:
                        raw = self.store.row(record["id"])
                        rows.append(self.store.encode_row(raw, self._now().date()))
                    except Exception as error:
                        if getattr(error, "status", None) != 404:
                            raise
                        fact = self.portable_problem(record['id'])
                        if fact and isinstance(fact.get('row'), dict):
                            rows.append(dict(fact['row'], id=record['id']))
        preferred, keys = {}, {}
        for row in rows:
            key = canonical_url(row.get("url"))
            keys[row['id']] = key
            if key and (key not in preferred or preferred[key].get("source") == "remote" and row.get("source") != "remote"):
                preferred[key] = row
        aliases = {row["id"]: preferred[keys[row['id']]]["id"] if keys[row['id']] else row["id"] for row in rows}
        for row in rows:
            from catalog_identity import remote_aliases
            for alias in [*row.get('aliasIds', []), *remote_aliases(row)]:
                aliases[alias] = aliases[row['id']]
        if scoped is not None:
            scoped['aliases'] = aliases
        return aliases

    def _equivalent_ids(self, identity):
        aliases = self._identity_map()
        canonical = aliases.get(identity, identity)
        return sorted({identity} | {other for other, target in aliases.items() if target == canonical})

    def start_training(self, identity, *, assisted=False):
        # One catalog snapshot for activation, aliases, review scheduling and the
        # returned workspace; repeated full catalog decoding delays single tasks.
        with self.lock, self._library_view():
            self._row(identity)
            if assisted:
                self.assert_solution_unlocked(identity)
            with self._write() as connection:
                self._claim_training(connection, identity)
                self._activate(connection, identity, iso(self._now()))
            if assisted:
                self.mark_solution_seen(identity)
            workspace = self.workspace()
            canonical = self._identity_map().get(identity, identity)
            task = next((row.get('reviewTask') for row in workspace['training'] if row['id'] == canonical), None)
            return {"workspace": workspace, "reviewTask": task}

    def review_plan(self):
        from reviews import ReviewScheduler
        return ReviewScheduler(self).plan()

    def review_task(self, identity, review_id, contest_id=None, open_task=False):
        from reviews import ReviewScheduler
        return ReviewScheduler(self).task(identity, review_id, contest_id, open_task)

    def remove_training(self, identity):
        with self.lock:
            self._row(identity)
            try:
                self.assert_solution_unlocked(identity)
            except ServiceError as error:
                if error.status != 403:
                    raise
                raise ServiceError(409, "这道题正在模拟赛中，交卷后才能取消训练") from error
            ids = self._equivalent_ids(identity)
            placeholders = ",".join("?" for _ in ids)
            if self.connection.execute(f"SELECT 1 FROM submissions WHERE problem_id IN ({placeholders}) AND finished_at IS NULL", ids).fetchone():
                raise ServiceError(409, "这道题还有评测任务，请等待结果后取消训练")
            if self.connection.execute(f"SELECT 1 FROM training WHERE id IN ({placeholders}) AND active=1", ids).fetchone():
                with self._write() as connection:
                    connection.execute(f"UPDATE training SET active=0,removed_at=? WHERE id IN ({placeholders})", [iso(self._now())] + ids)
            return {"workspace": self.workspace()}

    def clear_training(self):
        with self.lock:
            self._expire()
            if self.active_contest():
                raise ServiceError(409, "模拟赛正在进行，交卷后才能清空训练")
            if self.connection.execute("SELECT 1 FROM submissions WHERE finished_at IS NULL").fetchone():
                raise ServiceError(409, "还有评测任务，请等待结果后清空训练")
            count=self.connection.execute("SELECT COUNT(*) FROM training WHERE active=1").fetchone()[0]
            if count:
                with self._write() as connection:
                    connection.execute("UPDATE training SET active=0,removed_at=? WHERE active=1",(iso(self._now()),))
            return {"cleared":count,"workspace":self.workspace()}

    def save_official_pending(self, record):
        """持久化未完成官方回执，供返回 TB / 重启后恢复查询。"""
        if not isinstance(record, dict) or not record.get("sessionId"):
            return False
        submission_id = str(record.get("submissionId") or "")
        if not submission_id.isdecimal():
            return False
        with self.lock:
            identity = hashlib.sha256((str(record.get("sessionId")) + ":" + submission_id).encode()).hexdigest()
            with self._write() as connection:
                connection.execute("INSERT INTO official_pending(id,session_id,submission_id,problem_id,url,code,platform,accepted_at) "
                                   "VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET accepted_at=excluded.accepted_at",
                                   (identity, str(record.get("sessionId")), submission_id, record.get("problemId") or "",
                                    record.get("url") or "", record.get("code") or "", record.get("platform") or "", record.get("acceptedAt") or ""))
        return True

    def clear_official_pending(self, url=None, code=None):
        """官方回执已落库后清理对应 pending。"""
        from insights import canonical_url
        key = canonical_url(url)
        with self.lock:
            rows = self.connection.execute("SELECT id,url FROM official_pending").fetchall()
            remove = [row["id"] for row in rows if key and canonical_url(row["url"]) == key]
            if remove:
                with self._write() as connection:
                    connection.executemany("DELETE FROM official_pending WHERE id=?", [(item,) for item in remove])

    def official_pending(self, url, code):
        """返回与本机未完成官方回执对应的会话恢复信息（题目 URL 匹配）。"""
        from insights import canonical_url
        key = canonical_url(url)
        if not key:
            return []
        with self.lock:
            rows = self.connection.execute("SELECT * FROM official_pending").fetchall()
            result = []
            for row in rows:
                if canonical_url(row["url"]) != key:
                    continue
                result.append({"id": row["problem_id"], "url": row["url"], "submissionId": row["submission_id"],
                               "sessionId": row["session_id"], "code": row["code"], "acceptedAt": row["accepted_at"]})
            return result

    def record_official(self, session, receipt):
        from insights import canonical_url
        from urllib.parse import urlsplit
        remote=str(receipt.get('submissionId') or '')
        verdict=receipt.get('verdict')
        if receipt.get('status')!='finished' or not remote.isdecimal() or verdict not in (FAILURES-{'ERROR'})|{'AC'}:
            return None
        with self.lock:
            row=self._row(session['id'])
            from reviews import ReviewScheduler
            reviews = ReviewScheduler(self)
            review_id = session.get('reviewId') or reviews.read('review-session:' + str(session.get('sessionId', '')))
            review = self.review_task(row['id'], review_id, session.get('contestId')) if review_id else None
            key=canonical_url(session['url'])
            if not key or canonical_url(row.get('url') or self._asset_library().problem(row['id']).get('url'))!=key:
                raise ServiceError(409,"官方回执与本题不一致")
            contest = self.assert_official_allowed(row['id'], session.get('contestId'), receipt=True)
            accepted_at = receipt.get('acceptedAt') or session.get('acceptedAt')
            try:
                submitted = iso(parse_time(accepted_at)) if accepted_at else iso(self._now())
            except (ValueError, TypeError, AttributeError):
                submitted = iso(self._now())
            contest_id = None
            if contest and contest['started_at'] <= submitted <= min(contest['deadline'], contest['finished_at'] or contest['deadline']):
                contest_id = contest['id']
            identity='official-'+hashlib.sha256((str(urlsplit(session['url']).hostname)+'/'+remote).encode()).hexdigest()
            existing=self.connection.execute('SELECT * FROM submissions WHERE id=?',(identity,)).fetchone()
            if existing:
                # A public receipt may arrive before the bound browser job.
                # Enrich its missing code when the actual submitted code arrives.
                if not existing['code'] and session.get('code'):
                    with self._write() as connection:
                        connection.execute('UPDATE submissions SET code=? WHERE id=?', (self._code(session['code']), identity))
                if contest_id and not existing['contest_id'] and contest['started_at'] <= existing['submitted_at'] <= min(contest['deadline'], contest['finished_at'] or contest['deadline']):
                    with self._write() as connection:
                        connection.execute('UPDATE submissions SET contest_id=? WHERE id=? AND contest_id IS NULL', (contest_id, identity))
                        self._recompute_progress(connection, row['id'])
                if review:
                    with self._write() as connection:
                        reviews.bind(connection, identity, review_id)
                        if review.get('openedAt') and existing['submitted_at'] >= review['openedAt']:
                            connection.execute('UPDATE submissions SET solution_seen=? WHERE id=?', (int(reviews.assisted(row['id'], review, existing['submitted_at'])), identity))
                            self._recompute_progress(connection, row['id'])
                return self._submission(self.connection.execute('SELECT * FROM submissions WHERE id=?', (identity,)).fetchone())
            finished = iso(self._now())
            with self._write() as connection:
                if contest and contest['deleted_at']:
                    connection.execute('INSERT OR IGNORE INTO training(id,active_at,active) VALUES(?,?,0)', (row['id'], submitted))
                else:
                    self._activate(connection,row['id'],submitted)
                # 独立性以“受理时刻是否在看过题解之后”判定：看题解时间早于本次受理 = 看过题解。
                seen_row=connection.execute('SELECT solution_seen_at FROM training WHERE id=?',(row['id'],)).fetchone()
                seen_at=seen_row[0] if seen_row else None
                seen=bool(seen_at and seen_at<submitted)
                if review:
                    seen = reviews.assisted(row['id'], review, submitted)
                connection.execute("INSERT INTO submissions(id,problem_id,contest_id,mode,code,submitted_at,finished_at,verdict,scope,message,solution_seen) VALUES(?,?,?,'submit',?,?,?,?, 'official',?,?)",
                    (identity,row['id'],contest_id,self._code(session['code']),submitted,finished,verdict,'原站确认提交 #'+remote+(' · 官网同步（未取得源码）' if session.get('external') else ''),int(seen)))
                reviews.bind(connection, identity, review_id)
                self._recompute_progress(connection,row['id'])
            result = self._submission(self.connection.execute('SELECT * FROM submissions WHERE id=?',(identity,)).fetchone())
        if verdict == 'AC':
            self.leaderboard.invalidate()
        return result

    def insights(self, hub=None):
        with self.lock:
            # UI polls and the leaderboard share this read. Writes, library
            # changes, account switches and the Beijing date invalidate it.
            from copy import deepcopy
            signature = self._insights_signature(hub)
            cache = getattr(self, '_insights_cache', None)
            if signature is not None and cache and time.monotonic() - cache[0] < 30 and cache[1] == signature:
                result = deepcopy(cache[2])
                result['growth']['newAchievementXp'] = 0
                return result
            return self._compute_insights(hub)

    def _compute_insights(self, hub=None):
        from copy import deepcopy
        from insights import build_insights
        with self.lock, self._library_view():
            workspace = self.workspace()
            records = [dict(record) for record in self.connection.execute("SELECT * FROM submissions WHERE mode='submit' AND finished_at IS NOT NULL ORDER BY submitted_at,rowid")]
            history = [dict(record) for record in self.connection.execute("SELECT * FROM training")]
            library = self._library()
            known = {row["id"] for row in library}
            for record in history:
                if record["id"] not in known:
                    try:
                        library.append(self._row(record["id"]))
                    except Exception as error:
                        if getattr(error, "status", None) != 404:
                            raise
            value = build_insights(library, records, history, workspace, hub or {}, self._now())
            tasks = self.daily_tasks(goal_tasks=workspace.get('goalTasks', []))
            # 只累加版本 2（官方口径）任务的经验；旧本地任务领取保留在库里但不再计入成长。
            claimed = self.connection.execute("SELECT COALESCE(SUM(awarded_xp),0) AS xp,COUNT(*) AS count,MAX(claimed_at) AS latest FROM daily_missions WHERE claimed_at IS NOT NULL AND definition LIKE '%\"version\": 2%'").fetchone()
            from progression import official_reward_evidence, extra_achievements, qualified_contests
            evidence = official_reward_evidence(library, records, hub or {})
            completed = qualified_contests(workspace["contests"], records)
            claimed_dates = [item["claimed_at"] for item in self.connection.execute("SELECT claimed_at FROM daily_missions WHERE claimed_at IS NOT NULL ORDER BY claimed_at,rowid")]
            value["achievements"].extend(extra_achievements(evidence, records, completed, value["summary"]["longestStreak"], claimed_dates))
            from achievement_rewards import award_achievement_xp
            from progression import ACHIEVEMENT_DEFINITIONS, earned_titles
            awarded = {item[0] for item in self.connection.execute('SELECT achievement_id FROM achievement_xp_claims')}
            new_achievements = any(item.get('unlocked') and item['id'] in ACHIEVEMENT_DEFINITIONS and item['id'] not in awarded
                                   and not (item['id'] == 'streak-730' and 'streak-1000' in awarded)
                                   for item in value['achievements'])
            if new_achievements:
                with self._write() as connection:
                    achievement_rewards = award_achievement_xp(connection, value['achievements'], self._now())
            else:
                achievement_rewards = award_achievement_xp(self.connection, value['achievements'], self._now())
            ranking_profile = self._ranking_profile()
            ranking_reward = self.connection.execute("SELECT total_xp FROM ranking_reward_totals WHERE endpoint=? AND user_id=?",
                                                     (ranking_profile["endpoint"], ranking_profile["user_id"])).fetchone()
            ranking_xp = ranking_reward["total_xp"] if ranking_reward else 0
            xp = self._first_acceptance_xp(library, records) + claimed["xp"] + ranking_xp + achievement_rewards['xp']
            from tb_rank import growth, ranked
            value['growth'] = dict(growth(xp), missionXp=claimed['xp'], rankingXp=ranking_xp,
                                   achievementXp=achievement_rewards['xp'], newAchievementXp=achievement_rewards['newXp'])
            titles, equipped_titles = earned_titles(achievement_rewards['claims'])
            value.update(titles=titles, equippedTitles=equipped_titles)
            value['growth'].update(titles=titles, equippedTitles=equipped_titles)
            rank_profile = self.connection.execute('SELECT unlocked_at FROM tb_rank_profile WHERE id=1').fetchone()
            if value['growth']['rankedEligible'] and not rank_profile:
                with self._write() as connection:
                    connection.execute('INSERT OR IGNORE INTO tb_rank_profile VALUES(1,?)', (iso(self._now()),))
            rank_profile = self.connection.execute('SELECT unlocked_at FROM tb_rank_profile WHERE id=1').fetchone()
            if rank_profile:
                # Keep the original unlock without rewriting XP-based level.
                # Level and skill remain independent after the level-5 gate.
                value['growth']['rankedEligible'] = True
                per_day = {}
                from progression import local_date
                for record in records:
                    day = local_date(record.get('submitted_at'))
                    if day:
                        per_day.setdefault(day, []).append(record)
                daily_evidence = [item for daily_records in per_day.values()
                                  for item in official_reward_evidence(library, daily_records)]
                value['growth']['ranked'] = ranked(evidence, daily_evidence, rank_profile['unlocked_at'], self._now())
                if value['growth']['ranked']['qualified']:
                    value['growth'].update(tier=value['growth']['ranked']['tier'], badge=value['growth']['ranked']['badge'])
            value["dailyTasks"] = tasks
            value["profile"] = self.profile()["profile"]
            if self.admin_mode:
                from admin import decorate
                decorate(self, value)
            from progression import public_progress
            self._public_progress_cache = (time.monotonic(), self._public_progress_signature(hub or {}), public_progress(value))
            signature = self._insights_signature(hub)
            self._insights_cache = (time.monotonic(), signature, deepcopy(value))
            return value

    def _insights_signature(self, hub):
        library = getattr(self.store, 'library', None)
        if not callable(getattr(library, 'content_signature', None)):
            return None
        content = self.store._content_signature() if callable(getattr(self.store, '_content_signature', None)) else library.content_signature()
        if content is None:
            return None
        analysis = self.store._analysis_signature() if callable(getattr(self.store, '_analysis_signature', None)) else {}
        expired = self.connection.execute("SELECT 1 FROM contests WHERE status='running' AND deadline<=? LIMIT 1", (iso(self._now()),)).fetchone() is not None
        return id(self.connection), self._public_progress_signature(hub or {}), content, tuple(sorted(analysis.items())), expired

    def _public_progress_signature(self, hub):
        profiles = hashlib.sha256(json.dumps(hub.get('accounts', []), ensure_ascii=False, sort_keys=True).encode()).digest()
        return (self.connection.total_changes, self.connection.execute('PRAGMA data_version').fetchone()[0],
                self._now().astimezone(TRAINING_ZONE).date(), profiles)

    def public_progress(self):
        """Cached small leaderboard card, computed from the same growth evidence.

        A short cache avoids duplicate background/UI calculations. Local writes,
        public account replacement and the Beijing date immediately invalidate
        it; the five-second bound also catches new public library metadata.
        """
        from copy import deepcopy
        extensions = getattr(self.store, 'extensions', None)
        with self.lock:
            hub = extensions.snapshot() if callable(getattr(extensions, 'snapshot', None)) else {}
            cache = getattr(self, '_public_progress_cache', None)
            if cache and time.monotonic() - cache[0] < 5 and cache[1] == self._public_progress_signature(hub):
                return deepcopy(cache[2])
            self.insights(hub)
            return deepcopy(self._public_progress_cache[2])

    def _first_acceptance_xp(self, library, records):
        """Freeze earned awards; later difficulty corrections never subtract XP."""
        from progression import official_reward_evidence, official_first_xp, legacy_first_xp
        evidence = official_reward_evidence(library, records)
        migrating = not self.connection.execute('SELECT 1 FROM official_xp_state WHERE id=1').fetchone()
        legacy = legacy_first_xp() if migrating else {}
        cached_legacy = getattr(getattr(self.store, 'extensions', None), 'legacy_first_xp', None)
        if migrating and callable(cached_legacy):
            for key, amount in cached_legacy().items():
                legacy[key] = max(legacy.get(key, 0), amount)
        awards = {row['problem_key']: row['awarded_xp'] for row in self.connection.execute('SELECT * FROM official_first_xp_awards')}
        total = 0
        changes = []
        for item in evidence:
            key = item['key']
            current = official_first_xp(item.get('difficulty'))
            amount = awards.get(key)
            if amount is None:
                amount = legacy.get(key, current) if migrating else current
                if amount == 0:
                    amount = current
                changes.append(('INSERT INTO official_first_xp_awards VALUES(?,?,?)', (key, item['acceptedAt'], amount)))
            elif amount == 0 and current > 0:
                amount = current
                changes.append(('UPDATE official_first_xp_awards SET awarded_xp=? WHERE problem_key=?', (amount, key)))
            total += amount
        if changes or migrating:
            with self._write() as connection:
                for query, parameters in changes:
                    connection.execute(query, parameters)
                if migrating:
                    connection.execute('INSERT INTO official_xp_state VALUES(1,?)', (iso(self._now()),))
        return total

    def _evidence(self, day=None, *, hub=None):
        """Unique official ACs; daily rewards deduplicate within the requested day."""
        from progression import official_reward_evidence, local_date
        rows = self._library()
        known = {row["id"] for row in rows}
        records = [dict(record) for record in self.connection.execute("SELECT * FROM submissions WHERE mode='submit' AND verdict='AC' AND scope='official' AND finished_at IS NOT NULL ORDER BY submitted_at,rowid")]
        for record in records:
            if record["problem_id"] not in known:
                try:
                    rows.append(self._row(record["problem_id"]))
                    known.add(record["problem_id"])
                except Exception as error:
                    if getattr(error, "status", None) != 404:
                        raise
        extensions = getattr(self.store, "extensions", None)
        if hub is None and extensions is not None:
            snapshot = getattr(extensions, "snapshot", None)
            if callable(snapshot):
                hub = snapshot()
        if day is not None:
            records = [record for record in records if str(local_date(record['submitted_at'])) == day]
        return official_reward_evidence(rows, records, hub)

    def _daily_evidence(self, day):
        from copy import deepcopy
        extensions = getattr(self.store, 'extensions', None)
        hub = extensions.snapshot() if callable(getattr(extensions, 'snapshot', None)) else {}
        signature = self._insights_signature(hub)
        cached = getattr(self, '_daily_evidence_cache', None)
        if signature is not None and cached and cached[1:3] == (day, signature) and time.monotonic()-cached[0] < 5:
            return deepcopy(cached[3])
        evidence = self._evidence(day, hub=hub)
        self._daily_evidence_cache = (time.monotonic(), day, signature, deepcopy(evidence))
        return evidence

    def daily_tasks(self, goal_tasks=None, *, _evidence_snapshot=None):
        from progression import TASKS, SHANGHAI, task_progress
        with self.lock:
            day = self._now().astimezone(SHANGHAI).date().isoformat()
            current = {task["id"]: json.dumps(task, ensure_ascii=False) for task in TASKS}
            existing = {record["id"]: record for record in self.connection.execute("SELECT * FROM daily_missions WHERE day=?", (day,))}
            changes = [task for task in TASKS if task['id'] not in existing or
                       existing[task['id']]['claimed_at'] is None and existing[task['id']]['definition'] != current[task['id']]]
            if changes:
                # Reading a settled daily task list must not make another full
                # database backup or open a write transaction on each poll.
                with self._write() as connection:
                    for task in changes:
                        if task["id"] not in existing:
                            connection.execute("INSERT OR IGNORE INTO daily_missions(day,id,definition) VALUES(?,?,?)", (day, task["id"], current[task["id"]]))
                        else:
                            connection.execute("UPDATE daily_missions SET definition=? WHERE day=? AND id=?", (current[task["id"]], day, task["id"]))
            evidence = self._daily_evidence(day) if _evidence_snapshot is None else _evidence_snapshot
            tasks = []
            for record in self.connection.execute("SELECT * FROM daily_missions WHERE day=? ORDER BY rowid", (day,)):
                task = json.loads(record["definition"])
                progress, _ = task_progress(task, evidence, day)
                task.update(progress=progress, completed=progress >= task["target"], claimed=bool(record["claimed_at"]), claimedAt=record["claimed_at"])
                tasks.append(task)
            if goal_tasks is None:
                from goals import Goals
                goal_tasks = Goals(self).list(assign=True).get('goalTasks', [])
            return {"date": day, "timezone": "Asia/Shanghai", "tasks": tasks, "goalTasks": goal_tasks, "goalPending": sum(not task['accepted'] for task in goal_tasks), "claimable": sum(task["completed"] and not task["claimed"] for task in tasks),
                    "totalClaimedXp": sum(task["xp"] for task in tasks if task["claimed"]), "notice": "每日按北京时间刷新，统计当天官方 AC 的不同题目；旧题重新 AC 可计入，同题当天只算一次，样例通过和仅打开题目不计入。"}

    def claim_daily_task(self, identity, date=None):
        from progression import task_progress
        if not isinstance(identity, str) or not identity or len(identity) > 64:
            raise ServiceError(400, "每日任务编号无效")
        with self.lock:
            day = self._now().astimezone(TRAINING_ZONE).date().isoformat()
            evidence_snapshot = self._daily_evidence(day)
            tasks = self.daily_tasks(goal_tasks=[], _evidence_snapshot=evidence_snapshot)
            if date is not None and date != tasks["date"]:
                raise ServiceError(409, "每日任务已刷新，请重新打开任务列表")
            record = self.connection.execute("SELECT * FROM daily_missions WHERE day=? AND id=?", (tasks["date"], identity)).fetchone()
            if not record:
                raise ServiceError(404, "没有找到这项每日任务")
            already = bool(record["claimed_at"])
            if not already:
                with self._write() as connection:
                    task = json.loads(record["definition"])
                    progress, evidence = task_progress(task, evidence_snapshot, tasks["date"])
                    if progress < task["target"]:
                        raise ServiceError(409, "这项任务尚未完成")
                    connection.execute("UPDATE daily_missions SET claimed_at=?,awarded_xp=?,evidence=? WHERE day=? AND id=? AND claimed_at IS NULL",
                                       (iso(self._now()), task["xp"], json.dumps(evidence), tasks["date"], identity))
            # The durable claim is the response barrier. Heavy growth and
            # achievement calculations happen on the next background read.
            if not already:
                for item in tasks['tasks']:
                    if item['id'] == identity:
                        item.update(claimed=True, claimedAt=iso(self._now()))
                tasks['claimable'] = sum(item['completed'] and not item['claimed'] for item in tasks['tasks'])
                tasks['totalClaimedXp'] = sum(item['xp'] for item in tasks['tasks'] if item['claimed'])
            return {"dailyTasks": tasks, "awardedXp": 0 if already else task['xp'], "alreadyClaimed": already}

    def _ranking_profile(self):
        with self.lock:
            record = dict(self.connection.execute("SELECT * FROM ranking_profile WHERE singleton=1").fetchone())
        if self.account_provider is not None:
            auth = self.account_provider(record['user_id'])
            record['auth_token'] = auth['auth_token'] if auth else ''
            record['endpoint'] = auth['endpoint'] if auth else record['endpoint']
        return record

    def legacy_token(self):
        with self.lock:
            return self.connection.execute('SELECT auth_token FROM ranking_profile WHERE singleton=1').fetchone()[0]

    def bind_account(self, account, endpoint):
        with self.lock:
            previous = self.connection.execute('SELECT user_id,nickname,auth_token,endpoint FROM ranking_profile WHERE singleton=1').fetchone()
            values = (account['userId'], account['nickname'], '', endpoint)
            if not previous or tuple(previous) != values:
                with self._write() as connection:
                    connection.execute('UPDATE ranking_profile SET user_id=?,nickname=?,auth_token=?,endpoint=? WHERE singleton=1', values)
        if not self.jobs_started:
            self.jobs_started = True
            with self.lock:
                pending = self.connection.execute('SELECT id FROM submissions WHERE finished_at IS NULL').fetchall()
            for record in pending:
                self._enqueue(record['id'])

    def _ranking_rewards(self, profile, value):
        xp = value.get("totalXp")
        if value.get("userId") != profile["user_id"] or type(xp) is not int or not 0 <= xp <= 1_000_000_000:
            raise RuntimeError("排行榜经验响应无效")
        awards = value.get("awards", [])
        if not isinstance(awards, list) or len(awards) > 50:
            raise RuntimeError("排行榜奖励记录响应无效")
        with self.lock, self._write() as connection:
            connection.execute("""INSERT INTO ranking_reward_totals VALUES(?,?,?,?,?)
                ON CONFLICT(endpoint,user_id) DO UPDATE SET total_xp=excluded.total_xp,awards=excluded.awards,updated_at=excluded.updated_at""",
                (profile["endpoint"], profile["user_id"], xp, json.dumps(awards, ensure_ascii=False), iso(self._now())))

    def profile(self):
        record = self._ranking_profile()
        return {"profile": {"userId": record["user_id"], "nickname": record["nickname"], "displayName": record["nickname"], "createdAt": record["created_at"]},
                "leaderboard": self.leaderboard.snapshot()}

    def configure_profile(self, body):
        from leaderboard import validate_endpoint
        with self.lock:
            current = self._ranking_profile()
            nickname = body.get("nickname", current["nickname"])
            if not isinstance(nickname, str) or not 1 <= len(nickname.strip()) <= 32 or any(ord(char) < 32 or ord(char) == 127 for char in nickname):
                raise ServiceError(400, "昵称须为 1–32 个可显示字符")
            endpoint = validate_endpoint(body.get("endpoint", body.get("serverUrl", current["endpoint"])))
            with self._write() as connection:
                connection.execute("UPDATE ranking_profile SET nickname=?,endpoint=?,last_synced_at=CASE WHEN endpoint=? THEN last_synced_at ELSE NULL END WHERE singleton=1",
                                   (nickname.strip(), endpoint, endpoint))
        self.leaderboard.invalidate()
        return self.profile()

    def _ranking_events(self, endpoint):
        from progression import official_reward_evidence
        from insights import canonical_url
        with self.lock:
            records = [dict(row) for row in self.connection.execute(
                "SELECT * FROM submissions WHERE mode='submit' AND verdict='AC' AND scope='official' AND finished_at IS NOT NULL")]
            rows = {row["id"]: dict(row) for row in self._library()}
            for record in records:
                identity = record["problem_id"]
                if identity not in rows:
                    try:
                        rows[identity] = dict(self._row(identity))
                    except ServiceError as error:
                        if error.status != 404:
                            raise
                row = rows.get(identity)
                if row is not None and not canonical_url(row.get("url")):
                    try:
                        row["url"] = self._asset_library().problem(identity).get("url")
                    except (KeyError, ServiceError):
                        pass
            receipts = dict(self.connection.execute(
                "SELECT event_id,accepted_at FROM ranking_receipts WHERE endpoint=?", (endpoint,)))
            user = self._ranking_profile()["user_id"]
            events = []
            # Only persisted official submission receipts have a reliable date.
            # Public account summaries without a receipt are not fabricated into today's AC.
            for item in official_reward_evidence(list(rows.values()), records):
                event_id = hashlib.sha256(("official-v1\0" + user + "\0" + item["problemKey"]).encode()).hexdigest()
                previous = parse_time(receipts[event_id]) if event_id in receipts else None
                if previous and previous <= item["timestamp"]:
                    continue
                difficulty = item["difficulty"]
                events.append({"eventId": event_id, "problemKey": item["problemKey"],
                               "acceptedAt": item["acceptedAt"], "scope": "official",
                               "difficulty": difficulty if difficulty is not None and 0 <= difficulty <= 5000 else None})
            return events

    def _ranking_receipts(self, endpoint, events):
        with self._write() as connection:
            for event in events:
                connection.execute("INSERT INTO ranking_receipts VALUES(?,?,?) ON CONFLICT(endpoint,event_id) DO UPDATE SET accepted_at=excluded.accepted_at", (endpoint, event["eventId"], event["acceptedAt"]))

    def _ranking_synced(self, endpoint):
        with self._write() as connection:
            connection.execute("UPDATE ranking_profile SET last_synced_at=? WHERE singleton=1 AND endpoint=?", (iso(self._now()), endpoint))

    def start_practice_set(self, contest_name):
        if not isinstance(contest_name, str) or not contest_name.strip():
            raise ServiceError(400, "请选择一场原比赛")
        with self.lock:
            rows = [row for row in self._library() if row["contest"] == contest_name]
            if not rows:
                raise ServiceError(404, "这场比赛没有收录题目")
            existing = self.connection.execute("SELECT id FROM practice_sets WHERE name=?", (contest_name,)).fetchone()
            if not existing:
                identity = "practice-" + hashlib.sha256(contest_name.encode()).hexdigest()[:20]
                timestamp = iso(self._now())
                ids = [row["id"] for row in rows]
                with self._write() as connection:
                    connection.execute("INSERT INTO practice_sets VALUES(?,?,?,?)", (identity, contest_name, json.dumps(ids, ensure_ascii=False), timestamp))
                    for problem_id in ids:
                        self._claim_training(connection, problem_id)
                        self._activate(connection, problem_id, timestamp)
            else:
                identity = existing["id"]
                timestamp = iso(self._now())
                ids = [row["id"] for row in rows]
                old_ids = json.loads(self.connection.execute("SELECT ids FROM practice_sets WHERE id=?", (identity,)).fetchone()[0])
                needs_rejoin = any(not self.connection.execute("SELECT 1 FROM training WHERE id=? AND active=1", (problem_id,)).fetchone() for problem_id in ids)
                if needs_rejoin or old_ids != ids:
                    with self._write() as connection:
                        connection.execute("UPDATE practice_sets SET ids=? WHERE id=?", (json.dumps(ids, ensure_ascii=False), identity))
                        for problem_id in ids:
                            self._claim_training(connection, problem_id)
                            self._activate(connection, problem_id, timestamp)
            workspace = self.workspace()
            return {"set": next(item for item in workspace["sets"] if item["id"] == identity), "workspace": workspace}

    def _expire(self):
        now = iso(self._now())
        expired = self.connection.execute("SELECT * FROM contests WHERE status='running' AND deadline<=?", (now,)).fetchall()
        if expired:
            with self._write() as connection:
                for contest in expired:
                    self._finish_record(connection, contest, contest["deadline"])

    def _finish_record(self, connection, contest, finished_at):
        connection.execute("UPDATE contests SET status='finished',finished_at=? WHERE id=? AND status='running'", (finished_at, contest["id"]))
        replay = json.loads(contest['config'] or '{}').get('strategy') == 'replay'
        aliases = self._identity_map() if replay else {}
        solved = {aliases.get(row[0], row[0]) for row in connection.execute("SELECT problem_id FROM submissions WHERE contest_id=? AND mode='submit' AND ((?=0 AND scope='local' AND verdict IN ('AC','SAMPLE_PASS')) OR (scope='official' AND verdict='AC')) AND finished_at IS NOT NULL", (contest['id'], int(replay)))}
        for slot in json.loads(contest["slots"]):
            if aliases.get(slot['id'], slot['id']) not in solved:
                connection.execute("UPDATE training SET mock_due=1,mock_due_at=?,mock_due_context=? WHERE id=?", (finished_at, contest["id"], slot["id"]))

    def _contest_record(self, identity):
        if not isinstance(identity, str) or not identity:
            raise ServiceError(400, "缺少模拟赛编号")
        record = self.connection.execute("SELECT * FROM contests WHERE id=?", (identity,)).fetchone()
        if not record:
            raise ServiceError(404, "没有找到这场模拟赛")
        return record

    def active_contest(self):
        with self.lock:
            self._expire()
            record = self.connection.execute("SELECT * FROM contests WHERE status='running'").fetchone()
            return self._contest(record) if record else None

    def assert_solution_unlocked(self, identity):
        with self.lock:
            self._expire()
            active = self.connection.execute("SELECT slots FROM contests WHERE status='running'").fetchone()
            if active and identity in self._locked_ids(active):
                raise ServiceError(403, "模拟赛进行中，这道题的题解已锁定。交卷后可以复盘。")

    def assert_official_allowed(self, identity, contest_id=None, receipt=False):
        """All timed modes use native OJ forms in their validated contest context."""
        with self.lock:
            contest = self._context(identity, contest_id, writing=not receipt) if contest_id else None
            if contest:
                return contest
            active = self.connection.execute("SELECT * FROM contests WHERE status='running'").fetchone()
            if not contest and active and json.loads(active['config'] or '{}').get('strategy') == 'replay':
                if identity in self._locked_ids(active):
                    return None
            self.assert_solution_unlocked(identity)
            return None

    def _claim_training(self, connection, identity):
        """An explicit join gives a replay-created training entry its own life."""
        equivalents = set(self._equivalent_ids(identity))
        for contest in connection.execute("SELECT id,slots FROM contests WHERE deleted_at IS NULL").fetchall():
            slots = json.loads(contest['slots'])
            changed = False
            for slot in slots:
                if slot['id'] in equivalents and slot.get('trainingAdded'):
                    slot['trainingAdded'] = False
                    changed = True
            if changed:
                connection.execute('UPDATE contests SET slots=? WHERE id=?', (json.dumps(slots, ensure_ascii=False), contest['id']))

    def _locked_ids(self, active):
        """A remote/archive alias must not bypass the same original-question lock."""
        from insights import canonical_url
        slots = json.loads(active["slots"])
        locked = {slot["id"] for slot in slots}
        rows = self._library()
        extensions = getattr(self.store, "extensions", None)
        if extensions is not None:
            rows += extensions.rows()
        metadata = {row["id"]: row for row in rows}
        keys = set()
        for identity in locked:
            row = metadata.get(identity)
            if row is None:
                try:
                    row = self._row(identity)
                except Exception as error:
                    if getattr(error, "status", None) != 404:
                        raise
            key = canonical_url((row or {}).get("url"))
            if key:
                keys.add(key)
        locked.update(row["id"] for row in rows if canonical_url(row.get("url")) in keys)
        return locked

    def mark_solution_seen(self, identity):
        with self.lock:
            ids = self._equivalent_ids(identity)
            placeholders = ",".join("?" for _ in ids)
            record = self.connection.execute(f"SELECT solution_pending FROM training WHERE id IN ({placeholders})", ids).fetchone()
            if record:
                with self._write() as connection:
                    connection.execute(f"UPDATE training SET solution_pending=1,solution_seen_at=? WHERE id IN ({placeholders})", [iso(self._now())] + ids)
                    # 保留题解查看证据，不再强制进入重写队列。
                    self._recompute_progress(connection, identity)
            else:
                # Reading a solution before joining still affects independence,
                # while an inactive history row does not enlarge personal training.
                self._row(identity)
                timestamp = iso(self._now())
                with self._write() as connection:
                    connection.execute("INSERT INTO training(id,active_at,active,solution_pending,solution_seen_at) VALUES(?,?,0,1,?)", (identity, timestamp, timestamp))

    def _context(self, identity, contest_id, writing=False):
        self._expire()
        if contest_id:
            contest = self._contest_record(contest_id)
            if not any(slot["id"] == identity for slot in json.loads(contest["slots"])):
                raise ServiceError(403, "这道题不属于该模拟赛")
            if writing and contest["status"] != "running":
                raise ServiceError(409, "模拟赛已经结束，不能继续提交或改写考场草稿")
            return contest
        if writing:
            self.assert_solution_unlocked(identity)
        return None

    def problem(self, identity, contest_id=None, background=False, refresh=False, review_id=None):
        with self._library_view():
            return self._problem(identity, contest_id, background=background, refresh=refresh, review_id=review_id)

    def _problem(self, identity, contest_id=None, background=False, refresh=False, review_id=None):
        with self.lock:
            row = self._row(identity)
            self._context(identity, contest_id)
            self._history_visible(identity, contest_id)
            review = self.review_task(identity, review_id, contest_id, open_task=True)
        try:
            assets = self._asset_library()
            deferred = getattr(assets, 'background_problem', None)
            raw = deferred(identity, refresh=refresh) if background and callable(deferred) else assets.problem(identity)
        except (ValueError, RuntimeError, OSError) as error:
            raise ServiceError(422, "题面资源暂时无法读取：" + str(error)) from error
        with self.lock:
            if self.closed:
                raise ServiceError(503, "服务正在关闭，请稍后重试")
            self._context(identity, contest_id)
            self._history_visible(identity, contest_id)
            allowed = {"id", "title", "markdown", "url", "samples", "limits", "judge", "statementAvailable", "statementError", "statementLoading"}
            problem = {key: raw[key] for key in allowed if key in raw}
            problem.setdefault("id", identity)
            problem.setdefault("title", row["title"])
            problem.setdefault("markdown", None)
            problem.setdefault("url", None)
            problem.setdefault("samples", [])
            problem.setdefault("limits", {"timeMs": 2000, "memoryMb": 256})
            problem.setdefault("judge", {"scope": "samples", "label": "样例校验", "cases": len(problem["samples"])})
            problem.setdefault("statementAvailable", bool(problem["markdown"]))
            try:
                self.assert_solution_unlocked(identity)
                problem["locked"] = False
            except ServiceError as error:
                if error.status != 403:
                    raise
                problem["locked"] = True
            context = contest_id or ""
            if review:
                from reviews import task_context
                context = task_context(review_id)
            ids = self._equivalent_ids(identity)
            placeholders = ",".join("?" for _ in ids)
            draft = self.connection.execute(f"SELECT problem_id,code,saved_at,context FROM drafts WHERE problem_id IN ({placeholders}) AND context=? ORDER BY saved_at DESC LIMIT 1", ids + [context]).fetchone()
            if draft is None and not context:
                draft = self.connection.execute(f"SELECT problem_id,code,saved_at,context FROM drafts WHERE problem_id IN ({placeholders}) AND context IN (SELECT id FROM contests WHERE status='cancelled') ORDER BY saved_at DESC LIMIT 1", ids).fetchone()
            problem["draft"] = draft["code"] if draft else ""
            problem["draftLanguage"] = self._read_language(self._draft_language_key(draft["problem_id"] if draft else identity,draft['context'] if draft else context))
            if review and not draft:
                problem['draftLanguage'] = self._read_language(self._draft_language_key(identity, ''))
            problem["draftSavedAt"] = draft["saved_at"] if draft else None
            problem["submissions"] = self.submissions(identity, contest_id, exact_context=True, review_id=review_id)["submissions"]
            if review:
                problem['reviewTask'] = review
            if not problem["locked"]:
                from knowledge import enrich_row
                cache = getattr(self.store, "knowledge_analysis", None)
                evidence = {"statement":problem["markdown"], "official_tags":raw.get("officialTags")}
                analyzed = cache.enrich(row, **evidence) if cache is not None else enrich_row(row, **evidence)
                problem.update({key: analyzed[key] for key in ("tags", "knowledge", "knowledgeAnalysis") if key in analyzed})
            return problem

    @staticmethod
    def _code(code):
        if not isinstance(code, str) or len(code.encode("utf-8")) > MAX_CODE:
            raise ServiceError(400, "代码必须是文本，且大小不超过 64 KB")
        return code

    @staticmethod
    def _language(value):
        if value not in ('cpp17', 'python3'):
            raise ServiceError(400, '请选择 C++17 或 Python 3')
        return value

    @staticmethod
    def _draft_language_key(identity, context):
        return 'draft-language:' + hashlib.sha256((identity + '\0' + (context or '')).encode()).hexdigest()

    def _read_language(self, key):
        row = self.connection.execute('SELECT value FROM account_preferences WHERE key=?', (key,)).fetchone()
        return row['value'] if row and row['value'] in ('cpp17','python3') else 'cpp17'

    def _save_language(self, connection, key, language):
        previous=connection.execute('SELECT value FROM account_preferences WHERE key=?', (key,)).fetchone()
        if language!='cpp17' or previous:
            connection.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at', (key,language,iso(self._now())))

    def save_draft(self, identity, code, contest_id=None, language='cpp17', review_id=None):
        self._code(code)
        self._language(language)
        with self.lock:
            self._row(identity)
            self._context(identity, contest_id, writing=True)
            context = contest_id or ""
            if self.review_task(identity, review_id, contest_id, open_task=True):
                from reviews import task_context
                context = task_context(review_id)
            existing = self.connection.execute("SELECT code,saved_at FROM drafts WHERE problem_id=? AND context=?", (identity, context)).fetchone()
            if existing and existing["code"] == code and self._read_language(self._draft_language_key(identity,context)) == language:
                return {"savedAt": existing["saved_at"]}
            saved_at = iso(self._now())
            with self._write() as connection:
                self._save_language(connection,self._draft_language_key(identity,context),language)
                if not contest_id and not review_id and code.strip():
                    self._claim_training(connection, identity)
                connection.execute("INSERT INTO drafts VALUES(?,?,?,?) ON CONFLICT(problem_id,context) DO UPDATE SET code=excluded.code,saved_at=excluded.saved_at", (identity, context, code, saved_at))
            return {"savedAt": saved_at}

    def submit(self, identity, code, mode="submit", input_text="", contest_id=None, sample_run=None, language='cpp17', review_id=None):
        self._code(code)
        self._language(language)
        if mode not in ("run", "submit"):
            raise ServiceError(400, "操作类型必须是 run 或 submit")
        if not isinstance(input_text, str) or len(input_text.encode("utf-8")) > MAX_CODE:
            raise ServiceError(400, "运行输入不能超过 64 KB")
        if sample_run is not None and not isinstance(sample_run, bool):
            raise ServiceError(400, "样例运行选项必须是布尔值")
        sample_run = mode == "run" and (not input_text if sample_run is None else sample_run)
        if not code.strip():
            raise ServiceError(400, "请先输入代码")
        with self.lock:
            self._row(identity)
            contest = self._context(identity, contest_id, writing=True)
            review = self.review_task(identity, review_id, contest_id, open_task=True)
            if mode == 'submit' and contest and json.loads(contest['config'] or '{}').get('strategy') == 'replay':
                raise ServiceError(409, '重现赛请使用原站提交')
            if self.closed:
                raise ServiceError(503, "判题服务正在关闭，请稍后重试")
            pending = self.connection.execute("SELECT COUNT(*) FROM submissions WHERE finished_at IS NULL").fetchone()[0]
            if pending >= 16:
                raise ServiceError(429, "待判题任务较多，请等待已有提交完成")
        metadata = self._asset_library().problem(identity)
        with self.lock:
            if self.closed:
                raise ServiceError(503, "判题服务正在关闭，请稍后重试")
            pending = self.connection.execute("SELECT COUNT(*) FROM submissions WHERE finished_at IS NULL").fetchone()[0]
            if pending >= 16:
                raise ServiceError(429, "待判题任务较多，请等待已有提交完成")
            scope = metadata.get("judge", {}).get("scope", "samples")
            if scope not in ("local", "samples"):
                scope = "samples"
            submission_id = "submission-" + uuid.uuid4().hex
            # Asset lookups may take time; check the immutable server deadline again at receipt.
            contest = self._context(identity, contest_id, writing=True)
            timestamp = iso(self._now())
            if contest and timestamp >= contest["deadline"]:
                self._expire()
                raise ServiceError(409, "模拟赛已经到时，不能再接收提交")
            ids = self._equivalent_ids(identity)
            placeholders = ",".join("?" for _ in ids)
            training = self.connection.execute(f"SELECT MAX(solution_pending) AS solution_pending FROM training WHERE id IN ({placeholders})", ids).fetchone()
            seen_solution = int(bool(training and training["solution_pending"]))
            if review:
                from reviews import ReviewScheduler
                seen_solution = int(ReviewScheduler(self).assisted(identity, review, timestamp))
            with self._write() as connection:
                connection.execute("INSERT INTO submissions(id,problem_id,contest_id,mode,code,submitted_at,verdict,scope,custom_input,solution_seen,sample_run) VALUES(?,?,?,?,?,?,'QUEUED',?,?,?,?)", (submission_id, identity, contest_id or None, mode, code, timestamp, scope, input_text, seen_solution, int(sample_run)))
                self._save_language(connection, "submission-language:"+submission_id, language)
                if review:
                    ReviewScheduler(self).bind(connection, submission_id, review_id)
                if mode == "submit":
                    self._activate(connection, identity, timestamp)
            self._enqueue(submission_id)
            return {"submission": self._submission(self.connection.execute("SELECT * FROM submissions WHERE id=?", (submission_id,)).fetchone())}

    def _enqueue(self, identity):
        event = threading.Event()
        self.cancellations[identity] = event
        self.executor.submit(self._execute, identity, event)

    def _execute(self, identity, cancel):
        try:
            with self.lock:
                record = self.connection.execute("SELECT * FROM submissions WHERE id=?", (identity,)).fetchone()
                if record is None or record["finished_at"]:
                    return
                with self._write() as connection:
                    connection.execute("UPDATE submissions SET verdict='RUNNING' WHERE id=?", (identity,))
            try:
                execute = self._judge().execute
                options = {"mode": record["mode"], "input_text": record["custom_input"], "cancel": cancel}
                if "sample_run" in inspect.signature(execute).parameters:
                    options["sample_run"] = bool(record["sample_run"])
                if "language" in inspect.signature(execute).parameters:
                    options["language"] = self._read_language("submission-language:"+record["id"])
                result = execute(record["problem_id"], record["code"], **options)
            except Exception:
                logging.exception("TB judge execution failed")
                result = {"verdict": "ERROR", "scope": record["scope"], "message": "判题未完成，请检查本地编译器后重试"}
            if not isinstance(result, dict):
                result = {"verdict": "ERROR", "scope": record["scope"], "message": "判题结果格式无效"}
            verdict = result.get("verdict", "ERROR")
            scope = result.get("scope", record["scope"])
            if scope not in ("local", "samples"):
                scope = "samples"
            if verdict not in VERDICTS or verdict in ("QUEUED", "RUNNING"):
                verdict = "ERROR"
            # 2026-10-10：本地判题永不产生 AC；AC 只能来自 record_official（原站回执）。
            if verdict == "AC":
                verdict = "RUN_OK" if record["mode"] == "run" and not record["sample_run"] else "SAMPLE_PASS"
            case_results = self._case_results(result.get("caseResults", []))
            finished = iso(self._now())
            with self.lock:
                with self._write() as connection:
                    connection.execute("UPDATE submissions SET finished_at=?,verdict=?,scope=?,time_ms=?,memory_kb=?,passed=?,total=?,output=?,stderr=?,message=?,case_results=? WHERE id=?", (finished, verdict, scope, result.get("timeMs"), result.get("memoryKb"), max(0, int(result.get("passed", 0))), max(0, int(result.get("total", 0))), str(result.get("output", ""))[:262144], str(result.get("stderr", ""))[:262144], str(result.get("message", ""))[:4000], json.dumps(case_results, ensure_ascii=False), identity))
                    # 官方 AC 会推进个人进度；模赛提交完成后也要重算以清掉补题标记。
                    if record["mode"] == "submit" and (verdict == "AC" or record["contest_id"]):
                        self._recompute_progress(connection, record["problem_id"])
                self._expire()
        except Exception:
            logging.exception("TB submission persistence failed")
            # Persist an explicit terminal failure where possible; never leave a poller hanging.
            try:
                with self._write() as connection:
                    connection.execute("UPDATE submissions SET verdict='ERROR',finished_at=?,message=? WHERE id=? AND finished_at IS NULL", (iso(self._now()), "判题记录未能完整保存，请重试", identity))
            except Exception:
                logging.exception("TB could not persist terminal failure")
        finally:
            with self.lock:
                self.cancellations.pop(identity, None)

    def _recompute_progress(self, connection, identity):
        """Replay immutable received submissions, so asynchronous completion order is harmless.

        2026-10-10 口径变更：只有 scope='official' 的 AC 才算通过（本地样例全对
        只记 SAMPLE_PASS，不是 AC）。旧 local AC 的 accepted_at 派生值在重算时
        自然消失；原始提交记录永不删除。
        """
        ids = self._equivalent_ids(identity)
        placeholders = ",".join("?" for _ in ids)
        training_rows = connection.execute(f"SELECT * FROM training WHERE id IN ({placeholders})", ids).fetchall()
        if not training_rows:
            return
        accepted = connection.execute(f"SELECT * FROM submissions WHERE problem_id IN ({placeholders}) AND mode='submit' AND verdict='AC' AND scope='official' AND finished_at IS NOT NULL ORDER BY submitted_at,rowid", ids).fetchall()
        # 补题标记（mock_due）与 AC 来源无关：模赛里本地全过（含样例通过）也算完成该题。
        done = connection.execute(f"SELECT submitted_at,contest_id FROM submissions WHERE problem_id IN ({placeholders}) AND mode='submit' AND scope='local' AND verdict IN ('AC','SAMPLE_PASS') AND contest_id IS NOT NULL AND finished_at IS NOT NULL", ids).fetchall()
        if not accepted:
            # 没有官方 AC：清掉旧版本写入的本地通过派生值；补题标记仍按模赛完成情况清理。
            for training in training_rows:
                mock_due = training["mock_due"]
                if mock_due and any(row["contest_id"] == training["mock_due_context"] or not training["mock_due_at"] or row["submitted_at"] >= training["mock_due_at"] for row in done):
                    mock_due = 0
                connection.execute("UPDATE training SET accepted_at=NULL,review_count=0,rewrite_due=CASE WHEN solution_pending=1 THEN 1 ELSE rewrite_due END,mock_due=? WHERE id=?", (mock_due, training["id"]))
            return
        first, last = accepted[0], accepted[-1]
        cursor, review_at, reviews = first["submitted_at"], None, 0
        for submission in accepted[1:]:
            if not submission["solution_seen"] and (parse_time(submission["submitted_at"]) - parse_time(cursor)).total_seconds() >= 86400:
                reviews += 1
                cursor = review_at = submission["submitted_at"]
        for training in training_rows:
            # 需要独立重写的情形：最近一次 AC 是在看过题解之后提交的，
            # 或在最近一次 AC 之后才补看了题解。
            after_ac = bool(training["solution_seen_at"] and training["solution_seen_at"] >= last["submitted_at"])
            rewrite_due = bool(last["solution_seen"]) or after_ac
            mock_due = training["mock_due"]
            candidates = list(accepted) + list(done)
            if mock_due and any(row["contest_id"] == training["mock_due_context"] or not training["mock_due_at"] or row["submitted_at"] >= training["mock_due_at"] for row in candidates):
                mock_due = 0
            connection.execute("UPDATE training SET accepted_at=?,last_local_at=?,last_review_at=?,review_count=?,rewrite_due=?,solution_pending=?,mock_due=? WHERE id=?", (first["submitted_at"], last["submitted_at"], review_at, reviews, int(rewrite_due), int(rewrite_due), mock_due, training["id"]))

    @staticmethod
    def _case_results(values):
        if not isinstance(values, list):
            return []
        results, budget = [], 262144
        for value in values[:100]:
            if not isinstance(value, dict):
                continue
            case = {"name": str(value.get("name", "测试"))[:100], "input": "", "expected": None, "actual": "", "verdict": value.get("verdict") if value.get("verdict") in VERDICTS else "ERROR", "timeMs": value.get("timeMs"), "exitCode": value.get("exitCode"), "message": str(value.get("message", ""))[:500]}
            for field in ("input", "expected", "actual"):
                if value.get(field) is None and field == "expected":
                    continue
                raw = str(value.get(field, "")).encode("utf-8")[:min(65536, max(0, budget))]
                case[field] = raw.decode("utf-8", "ignore")
                budget -= len(raw)
            results.append(case)
        return results

    def _submission(self, record):
        return {"language":self._read_language("submission-language:"+record["id"]), "id": record["id"], "problemId": record["problem_id"], "contestId": record["contest_id"], "mode": record["mode"], "verdict": record["verdict"], "scope": record["scope"], "code": record["code"], "submittedAt": record["submitted_at"], "finishedAt": record["finished_at"], "timeMs": record["time_ms"], "memoryKb": record["memory_kb"], "passed": record["passed"], "total": record["total"], "output": record["output"], "stderr": record["stderr"], "message": record["message"], "sampleRun": bool(record["sample_run"]), "caseResults": json.loads(record["case_results"])}

    def submission(self, identity):
        with self.lock:
            self._expire()
            record = self.connection.execute("SELECT * FROM submissions WHERE id=?", (identity,)).fetchone()
            if not record:
                raise ServiceError(404, "没有找到这次提交")
            self._history_visible(record["problem_id"], record["contest_id"])
            result = {"submission": self._submission(record)}
            if record["finished_at"]:
                result["workspace"] = self.workspace()
            return result

    def submissions(self, identity=None, contest_id=None, exact_context=False, limit=100, offset=0, results_only=False, review_id=None, query='', verdict='', order='desc'):
        try:
            limit, offset = int(limit), int(offset)
        except (ValueError, TypeError):
            raise ServiceError(400, "提交记录分页参数无效")
        if not 1 <= limit <= 100 or offset < 0:
            raise ServiceError(400, "每页提交记录须为 1–100 条，偏移量不能为负")
        if not isinstance(query, str) or len(query) > 120 or order not in ('asc', 'desc'):
            raise ServiceError(400, '提交记录查询参数无效')
        if verdict not in ('', 'AC', 'WA', 'CE', 'TLE', 'MLE', 'RE', 'OLE', 'ERROR', 'QUEUED', 'RUNNING'):
            raise ServiceError(400, '提交结果筛选无效')
        with self.lock:
            self._expire()
            active = self.connection.execute("SELECT id,slots FROM contests WHERE status='running'").fetchone()
            locked = self._locked_ids(active) if active else set()
            if identity:
                self._history_visible(identity, contest_id)
            clauses, values = [], []
            if verdict:
                clauses.append('verdict=?')
                values.append(verdict)
            if query.strip():
                catalog = self._library()
                for token in query.casefold().split():
                    ids = set()
                    for row in catalog:
                        text = ' '.join(str(row.get(key) or '') for key in ('id', 'title', 'contest', 'problem')).casefold()
                        if token in text:
                            ids.update([row['id'], *row.get('aliasIds', [])])
                    candidates = sorted(ids)
                    match = ('problem_id IN (' + ','.join('?' for _ in candidates) + ') OR ') if candidates else ''
                    clauses.append('(' + match + 'instr(lower(verdict),?)>0 OR instr(lower(problem_id),?)>0)')
                    values.extend([*candidates, token, token])
            if review_id:
                if not identity:
                    raise ServiceError(400, '复习记录缺少题目编号')
                self.review_task(identity, review_id, contest_id)
                clauses.append("id IN (SELECT substr(key,16) FROM account_preferences WHERE key LIKE 'review-receipt:%' AND value=?)")
                values.append(json.dumps(review_id))
            if results_only:
                clauses.append("mode='submit' AND sample_run=0 AND verdict!='SAMPLE_PASS' AND (scope='official' OR scope='local')")
            if identity:
                ids = self._equivalent_ids(identity)
                clauses.append("problem_id IN (" + ",".join("?" for _ in ids) + ")")
                values.extend(ids)
            if contest_id:
                self._contest_record(contest_id)
                clauses.append("contest_id=?")
                values.append(contest_id)
            elif exact_context:
                clauses.append("contest_id IS NULL")
            if locked:
                clauses.append("(problem_id NOT IN (" + ",".join("?" for _ in locked) + ") OR contest_id=?)")
                values.extend(sorted(locked))
                values.append(active["id"])
            where = " WHERE " + " AND ".join(clauses) if clauses else ""
            total = self.connection.execute("SELECT COUNT(*) FROM submissions" + where, values).fetchone()[0]
            direction = 'ASC' if order == 'asc' else 'DESC'
            records = self.connection.execute("SELECT * FROM submissions" + where + f" ORDER BY submitted_at {direction},rowid {direction} LIMIT ? OFFSET ?", values + [limit, offset]).fetchall()
            catalog={row['id']:row for row in self._library()}
            aliases=self._identity_map(list(catalog.values()))
            submissions=[]
            for record in records:
                value=self._submission(record)
                canonical=aliases.get(value['problemId'],value['problemId'])
                row=catalog.get(canonical)
                if row:value.update(canonicalProblemId=canonical,title=row.get('title'),contestName=row.get('contest'),problem=row.get('problem'))
                submissions.append(value)
            return {"submissions": submissions, "total": total, "offset": offset, "limit": limit, "hasMore": offset + len(records) < total}

    def _history_visible(self, identity, context):
        active = self.connection.execute("SELECT id,slots FROM contests WHERE status='running'").fetchone()
        if active and context != active["id"] and identity in self._locked_ids(active):
            raise ServiceError(403, "这道题正在模拟赛中，请从当前考场打开；旧草稿和提交记录赛后恢复。")

    def _contest_options(self, body):
        if not isinstance(body, dict):
            raise ServiceError(400, "模拟赛参数无效")
        strategy = body.get("strategy", body.get("mode", "comprehensive"))
        if strategy not in ("comprehensive", "topic", "single"):
            raise ServiceError(400, "训练方式须为综合、专项或单题")
        tags = body.get("tags", [])
        topic = body.get("topic")
        if topic is not None:
            if not isinstance(topic, str):
                raise ServiceError(400, "专项知识点无效")
            if topic.strip():
                tags = [topic.strip()] if not tags else tags
        if not isinstance(tags, list) or len(tags) > 256 or not all(isinstance(tag, str) and 0 < len(tag.strip()) <= 80 for tag in tags):
            raise ServiceError(400, "请选择有效的专项知识点")
        tags = sorted(set(tag.strip() for tag in tags))
        if strategy == "topic" and not tags:
            raise ServiceError(400, "专项训练须选择至少一个知识点")
        platform = body.get("platform", "") or ""
        if not isinstance(platform, str) or len(platform) > 80:
            raise ServiceError(400, "题目平台无效")
        switches = {}
        for key in ("excludeSolved", "reviewedOnly"):
            value = body.get(key, False)
            if not isinstance(value, bool):
                raise ServiceError(400, "模拟赛筛选选项须为布尔值")
            switches[key] = value
        from contest_rules import rules
        return {"strategy": strategy, "tags": tags, "platform": platform.strip(), **switches, **rules(body)}

    def _solved_problem_keys(self, rows):
        # 2026-10-10：已解 = 官方 AC（含 hub 同步）。本地样例通过不算已解。
        from insights import canonical_url
        accepted = {item["key"] for item in self._evidence()}
        by_id={row['id']:row for row in rows}
        for item in self.connection.execute("SELECT problem_id FROM submissions WHERE mode='submit' AND verdict='AC' AND scope='official' AND finished_at IS NOT NULL"):
            accepted.add(canonical_url(by_id.get(item['problem_id'],{}).get('url')) or item['problem_id'])
        extensions = getattr(self.store, "extensions", None)
        if extensions is not None:
            snapshot = getattr(extensions, "snapshot", None)
            if callable(snapshot):
                for account in snapshot().get("accounts", []):
                    accepted.update(key for item in account.get("solved", []) if (key := canonical_url(item.get("url"))))
        return accepted

    @staticmethod
    def _eligible_contest_row(row, options, lower, upper, solved):
        from insights import canonical_url
        if row.get('catalogHidden'):
            return False
        difficulty = row.get("difficulty")
        if not isinstance(difficulty, (int, float)) or isinstance(difficulty, bool) or not lower <= difficulty <= upper:
            return False
        aliases = {"codeforces": "codeforces", "atcoder": "atcoder", "nowcoder": "牛客", "luogu": "洛谷"}
        platform = options["platform"].casefold()
        platform = aliases.get(platform, platform)
        from contest_categories import matches_shelf
        if platform and not matches_shelf(row,platform):
            return False
        scope=set(row.get('tags',[]))
        scope.update(part.strip() for path in row.get('knowledgeCategories',[]) for part in path.split(' / ') if part.strip())
        if options["tags"] and not set(options["tags"]) & scope:
            return False
        if options["excludeSolved"] and (canonical_url(row.get("url")) or row["id"]) in solved:
            return False
        return not options["reviewedOnly"] or row.get("judgeScope") == "local"

    def preview_contest(self, body):
        if isinstance(body,dict) and body.get('mode')=='replay':
            return self.preview_replay(body)
        options = self._contest_options(body)
        try:
            count = 1 if options["strategy"] == "single" else int(body.get("count", 6))
            lower, upper = int(body.get("min", 0)), int(body.get("max", 10000))
            band = 0 if upper <= 1400 else 1 if upper <= 1700 else 2 if upper <= 2000 else 3
            base = ([90, 120, 150, 180] if options['strategy'] == 'topic' else [120, 150, 180, 210])[band]
            default_duration = [30, 45, 60, 75][band] if options['strategy'] == 'single' else max(30, min(480, (base * count + 59) // 60 * 15))
            if 'mode' not in body:  # Preserve legacy clients' untyped preview contract.
                default_duration = 300 if options['rules'] == 'xcpc' else 120
            duration = int(body.get("duration", default_duration))
        except (ValueError, TypeError, AttributeError):
            raise ServiceError(400, "模拟赛参数无效")
        if not 1 <= count <= 20 or not 1 <= duration <= 1440 or not 0 <= lower <= upper <= 10000:
            raise ServiceError(400, "题数须为 1–20，时长须为 1–1440 分钟，难度上下限须有效")
        with self.lock:
            rows = self._library()
            active = {record["id"]: bool(record["accepted_at"]) for record in self.connection.execute("SELECT id,accepted_at FROM training WHERE active=1")}
            solved = self._solved_problem_keys(rows) if options["excludeSolved"] else set()
        eligible = self._asset_library().candidates(rows)
        with self.lock:
            seen = set()
            from insights import canonical_url
            eligible = [row for row in eligible if self._eligible_contest_row(row, options, lower, upper, solved)
                        and not ((canonical_url(row.get("url")) or row["id"]) in seen or seen.add(canonical_url(row.get("url")) or row["id"]))]
            available = len(eligible)
            if available < count:
                raise ServiceError(422, f"当前范围只有 {available} 道具备原题面和样例的题目，无法组成 {count} 题模拟赛。请扩大难度范围或减少题数。")
            levels = len({row["difficulty"] for row in eligible})
            if options["strategy"] == "comprehensive" and levels < count:
                raise ServiceError(422, f"当前可用题目只有 {levels} 档不同难度，无法组成 {count} 题递进模拟赛。请扩大难度范围或减少题数。")
            chosen, covered, main_tags, platforms = [], set(), set(), set()
            pool = list(eligible)
            random_rank = {row["id"]: self.rng.random() for row in eligible}
            # Persisted papers count as exposure, including deleted papers. A
            # mirror uses the same canonical key as its original problem.
            keys = {row['id']: canonical_url(row.get('url')) or row['id'] for row in rows}
            usage, latest, previews = {}, {}, {}
            for paper in self.connection.execute('SELECT slots,started_at FROM contests ORDER BY started_at'):
                for slot in json.loads(paper['slots']):
                    key = keys.get(slot['id'], slot['id'])
                    usage[key] = usage.get(key, 0) + 1
                    latest[key] = paper['started_at']
            for saved in self.previews.values():
                for slot in saved['slots']:
                    key = keys.get(slot['id'], slot['id'])
                    previews[key] = previews.get(key, 0) + 1
            def exposure(row):
                key = keys.get(row['id'], row['id'])
                return (bool(usage.get(key, 0) or previews.get(key, 0)), usage.get(key, 0) + previews.get(key, 0), latest.get(key, ''))
            band_width = max(100, (upper - lower) / count * .65)
            for index in range(count):
                center = lower + (upper - lower) * ((index + .5) / count)
                selected_difficulties = {row["difficulty"] for row in chosen}
                def score(row):
                    tags = row.get("tags", [])
                    main = tags[0] if tags else ""
                    fit = int(abs(row["difficulty"] - center) / band_width)
                    return (row["difficulty"] in selected_difficulties, fit // 2, exposure(row), bool(main and main in main_tags), active.get(row["id"], False), row["id"] in active, row.get("platform") in platforms, random_rank[row["id"]] - .06 * min(3, len(set(tags) - covered)), abs(row["difficulty"] - center), row["id"])
                eligible.sort(key=score)
                row = eligible.pop(0)
                chosen.append(row)
                covered.update(row.get("tags", []))
                if row.get("tags"):
                    main_tags.add(row["tags"][0])
                platforms.add(row.get("platform"))
            # When the reviewed pool permits, include a DP problem, a graph problem,
            # and a basic technique without flattening the difficulty progression.
            def families(row):
                tags = row.get("tags", [])
                result = set()
                if any("DP" in tag or "动态规划" in tag for tag in tags):
                    result.add("dp")
                if any(tag in {"图论", "BFS", "拓扑排序", "差分约束", "最短路", "并查集", "树", "树形 DP"} for tag in tags):
                    result.add("graph")
                if any(tag in {"模拟", "枚举", "贪心", "排序", "前缀和", "差分", "二分查找", "双指针"} for tag in tags):
                    result.add("basic")
                return result
            required = {family for family in ("dp", "graph", "basic") if options["strategy"] == "comprehensive" and count >= 3 and any(family in families(row) for row in pool)}
            for family in ("dp", "graph", "basic"):
                if family not in required or any(family in families(row) for row in chosen):
                    continue
                replacements = []
                for replacement in pool:
                    if replacement in chosen or family not in families(replacement):
                        continue
                    for index, current in enumerate(chosen):
                        if exposure(replacement) > exposure(current):
                            continue
                        alternate = chosen[:index] + [replacement] + chosen[index + 1:]
                        if len({row["difficulty"] for row in alternate}) != len({row["difficulty"] for row in chosen}):
                            continue
                        protected = required & set().union(*(families(row) for row in chosen))
                        if not protected <= set().union(*(families(row) for row in alternate)):
                            continue
                        replacements.append((exposure(replacement), int(abs(replacement["difficulty"] - current["difficulty"]) / band_width), random_rank[replacement["id"]], index, replacement))
                if replacements:
                    _, _, _, index, replacement = min(replacements, key=lambda option: option[:4])
                    chosen[index] = replacement
            chosen.sort(key=lambda row: (row["difficulty"], row["id"]))
            preview_key = (count, duration, lower, upper, json.dumps(options, sort_keys=True, ensure_ascii=False))
            previous = self.previous_previews.get(preview_key)
            if previous == tuple(row["id"] for row in chosen):
                alternatives = []
                protected = required & set().union(*(families(row) for row in chosen))
                for replacement in pool:
                    if replacement in chosen:
                        continue
                    for index, current in enumerate(chosen):
                        if exposure(replacement) > exposure(current):
                            continue
                        if abs(replacement["difficulty"] - current["difficulty"]) > band_width * 1.5:
                            continue
                        alternate = chosen[:index] + [replacement] + chosen[index + 1:]
                        if len({row["difficulty"] for row in alternate}) != len({row["difficulty"] for row in chosen}) or not protected <= set().union(*(families(row) for row in alternate)):
                            continue
                        alternatives.append((random_rank[replacement["id"]], index, replacement))
                if alternatives:
                    _, index, replacement = min(alternatives, key=lambda option: option[:2])
                    chosen[index] = replacement
                    chosen.sort(key=lambda row: (row["difficulty"], row["id"]))
            self.previous_previews[preview_key] = tuple(row["id"] for row in chosen)
            slots = [{"letter": chr(65 + index), "id": row["id"], "title": row["title"], "difficulty": row["difficulty"], "tags": row.get("tags", []), "judgeScope": row.get("judgeScope", "samples")} for index, row in enumerate(chosen)]
            name = f"模拟赛 · {len(slots)} 题 / {duration} 分钟"
            # The server retains full metadata, but the random preview stays blind.
            public_slots = [{key: slot[key] for key in ("letter", "id", "title", "judgeScope")} for slot in slots]
            repeated = sum(bool(exposure(row)[0]) for row in chosen)
            plan = {"previewId": uuid.uuid4().hex, "name": name, "slots": public_slots, "duration": duration, "min": lower, "max": upper, "strategy": options["strategy"], "constraints": options, "selectionNotice": f'当前范围的新题不足，本卷含 {repeated} 道曾抽取或练习的题目。' if repeated else ''}
            self.previews[tuple(slot["id"] for slot in slots)] = {"plan": plan, "slots": slots, "at": self._now()}
            while len(self.previews) > 20:
                self.previews.pop(next(iter(self.previews)))
            return {"plan": plan, "available": available}

    def replay_events(self):
        from contest_rules import event_info
        with self.lock:
            groups={}
            for row in self._library():
                if not row.get('catalogHidden') and row.get('source') != 'luogu-training':groups.setdefault(row['contest'],[]).append(row)
            result=[event_info(name,rows) for name,rows in groups.items()]
            from contest_names import contest_name, natural_key
            for item in result:
                item['displayName'] = contest_name(item['name'])
                event_rows=groups[item['name']]
                levels=sorted(row['difficulty'] for row in event_rows if isinstance(row.get('difficulty'), (int,float)))
                item['difficulty']=levels[len(levels)//2] if levels else None
                item['platform']=event_rows[0].get('platform','')
                item['series']=event_rows[0].get('series','')
                for key in ('contestDate','startedAt','endedAt','eventYear','examYear','examGroup','examStage','contestFullName','schoolTraining'):
                    value=next((row.get(key) for row in event_rows if row.get(key) is not None),None)
                    if value is not None:item[key]=value
            from graph_lab import replay_events
            result.extend(replay_events(self._library()))
            return {'events':sorted(result, key=lambda item: natural_key(item['displayName']))}

    def preview_replay(self, body):
        from contest_rules import event_info, rules
        import re
        name=body.get('contest')
        if not isinstance(name,str) or not name:raise ServiceError(400,'请选择已收录比赛')
        with self.lock:
            from graph_lab import replay_rows
            lab = replay_rows(name, self._library())
            rows=lab if lab is not None else [row for row in self._library() if row['contest']==name and row.get('source') != 'luogu-training']
            if not rows:raise ServiceError(404,'这场比赛尚未收录')
            info=event_info(name,rows)
            if lab is not None: info.update(complete=True, expectedCount=5, labTopic=name.split(' · ',1)[-1])
            if info['complete'] is False:raise ServiceError(422,'这场比赛题单尚不完整，请先收录剩余赛题')
            def order(row):
                return tuple((0,int(piece)) if piece.isdecimal() else (1,piece.upper()) for piece in re.findall(r'\d+|\D+',row['problem']))
            if lab is None: rows.sort(key=order)
        # Load missing public statements before freezing; never silently omit a slot.
        for row in rows:self._asset_library().problem(row['id'])
        available={row['id']:row for row in self._asset_library().candidates(rows)}
        missing=[row['problem'] for row in rows if row['id'] not in available]
        if missing:raise ServiceError(422,'以下题目尚缺完整题面或样例：'+', '.join(missing)+'。补全后才能重现整场已收录赛题')
        try:duration=int(body.get('duration',info['duration']))
        except (ValueError,TypeError):raise ServiceError(400,'重现赛时长无效')
        if not 1<=duration<=1440:raise ServiceError(400,'时长须为 1–1440 分钟')
        options={'strategy':'replay','contest':name,'tags':[],'platform':'','excludeSolved':False,'reviewedOnly':False,**rules({'rules':info['rules'],**body})}
        slots=[{'letter':chr(65+position) if lab is not None else row['problem'],'id':row['id'],'title':row['title'],'difficulty':row.get('difficulty'),'tags':row.get('tags',[]),'judgeScope':available[row['id']]['judgeScope']} for position,row in enumerate(rows)]
        plan={'previewId':uuid.uuid4().hex,'name':'重现赛 · '+name,'slots':[{key:slot[key] for key in ('letter','id','title','judgeScope')} for slot in slots],
              'duration':duration,'min':0,'max':10000,'strategy':'replay','constraints':options,'event':info}
        with self.lock:self.previews[tuple(slot['id'] for slot in slots)]={'plan':plan,'slots':slots,'at':self._now()}
        return {'plan':plan,'available':len(slots)}

    def start_contest(self, body):
        ids = body.get("ids")
        if not isinstance(ids, list) or not ids or len(ids) > 100 or not all(isinstance(identity, str) for identity in ids) or len(set(ids)) != len(ids):
            raise ServiceError(400, "请选择 1–100 道不重复的模拟赛题目")
        try:
            duration = int(body.get("duration", 120))
        except (ValueError, TypeError):
            raise ServiceError(400, "模拟赛时长无效")
        with self.lock, self._library_view():
            self._expire()
            if self.connection.execute("SELECT 1 FROM contests WHERE status='running'").fetchone():
                raise ServiceError(409, "已有一场模拟赛正在进行，请先回到考场或交卷")
            preview = self.previews.get(tuple(ids))
            if not preview or duration != preview["plan"]["duration"] or (self._now() - preview["at"]).total_seconds() > 1800:
                raise ServiceError(409, "选题预览已变化或过期，请重新生成并确认")
            if "previewId" in body and body["previewId"] != preview["plan"]["previewId"]:
                raise ServiceError(409, "选题预览已更新，请使用当前预览")
            options = preview["plan"]["constraints"]
            if options['strategy']=='replay' and any(key in body for key in ('strategy','mode','contest','rules','wrongPenalty','compilePenalty')):
                if any(body[key]!=options.get('strategy' if key=='mode' else key) for key in body if key in options or key=='mode'):raise ServiceError(409,'重现赛条件已变化，请重新预览')
            elif any(key in body for key in ("strategy", "mode", "tags", "topic", "platform", "excludeSolved", "reviewedOnly","rules","wrongPenalty","compilePenalty")):
                requested_body = {**options, **body}
                if "mode" in body and "strategy" not in body:
                    requested_body["strategy"] = body["mode"]
                if "topic" in body and "tags" not in body:
                    requested_body["tags"] = []
                requested = self._contest_options(requested_body)
                if requested != options:
                    raise ServiceError(409, "筛选条件已变化，请重新生成题目")
            if "count" in body and body["count"] != len(ids):
                raise ServiceError(409, "题数已变化，请重新生成题目")
            for key in ("min", "max"):
                if key in body and body[key] != preview["plan"][key]:
                    raise ServiceError(409, "难度条件已变化，请重新生成题目")
            solved = self._solved_problem_keys(self._library()) if options["excludeSolved"] else set()
            current_rows = {row["id"]: row for row in self._asset_library().candidates([self._row(identity) for identity in ids])}
            for identity in ids:
                row = current_rows.get(identity)
                if row is None:
                    raise ServiceError(409, "原题面或评测资料已变化，请重新生成题目")
                if options['strategy']!='replay' and not self._eligible_contest_row(row, options, preview["plan"]["min"], preview["plan"]["max"], solved):
                    raise ServiceError(409, "题目资料或通过状态已变化，请重新生成题目")
            name = body.get("name") or preview["plan"]["name"]
            if not isinstance(name, str) or len(name) > 100:
                raise ServiceError(400, "模拟赛名称过长")
            now = self._now()
            timestamp = iso(now)
            deadline = iso(now + dt.timedelta(minutes=duration))
            identity = "contest-" + uuid.uuid4().hex
            with self._write() as connection:
                owned = {slot['id'] for prior in connection.execute('SELECT slots,config FROM contests WHERE deleted_at IS NULL')
                         if json.loads(prior['config'] or '{}').get('strategy') == 'replay' for slot in json.loads(prior['slots']) if slot.get('trainingAdded')}
                slots = [dict(slot, trainingAdded=bool(set(self._equivalent_ids(slot['id'])) & owned) or not any(connection.execute('SELECT 1 FROM training WHERE id=? AND active=1', (other,)).fetchone()
                         for other in self._equivalent_ids(slot['id']))) for slot in preview['slots']]
                for slot in slots:
                    before = connection.execute('SELECT active,active_at,removed_at FROM training WHERE id=?', (slot['id'],)).fetchone()
                    slot['trainingBefore'] = dict(before) if before else None
                connection.execute("INSERT INTO contests(id,name,status,started_at,deadline,finished_at,duration,slots,config) VALUES(?,?,'running',?,?,NULL,?,?,?)", (identity, name, timestamp, deadline, duration, json.dumps(slots, ensure_ascii=False), json.dumps(options, ensure_ascii=False)))
                for problem_id in ids:
                    self._activate(connection, problem_id, timestamp)
            self.previews.pop(tuple(ids), None)
            return {"contest": self._contest(self._contest_record(identity)), "workspace": self.workspace()}

    def _contest(self, record):
        records = self.connection.execute("SELECT * FROM submissions WHERE contest_id=? AND mode='submit' ORDER BY submitted_at,rowid", (record["id"],)).fetchall()
        config = json.loads(record['config'] or '{}')
        aliases = self._identity_map()
        by_problem = {}
        for submission in records:
            by_problem.setdefault(aliases.get(submission['problem_id'], submission['problem_id']), []).append(submission)
        slots, penalty = [], 0
        for frozen in json.loads(record["slots"]):
            attempts = by_problem.get(aliases.get(frozen['id'], frozen['id']), [])
            # Replay counts original-site AC; blind mock exams also accept
            # reviewed local cases. Public samples never count as a solved slot.
            accepted = next((submission for submission in attempts if submission["finished_at"] and
                (submission['scope'] == 'official' and submission['verdict'] == 'AC' or
                 config.get('strategy') != 'replay' and submission['scope'] == 'local' and submission['verdict'] in ('AC', 'SAMPLE_PASS'))), None)
            latest = attempts[-1] if attempts else None
            sample_ok = accepted is not None or any(submission["finished_at"] and submission["verdict"] == "SAMPLE_PASS" for submission in attempts)
            slot = {"letter": frozen["letter"], "id": frozen["id"], "title": frozen["title"], "accepted": accepted is not None, "samplePassed": sample_ok, "verdict": latest["verdict"] if latest else None, "attempts": len(attempts), "solvedAt": accepted["submitted_at"] if accepted else None}
            if record["status"] == "finished":
                slot.update({key: frozen[key] for key in ("difficulty", "tags", "judgeScope")})
            if accepted:
                minutes = int((parse_time(accepted["submitted_at"]) - parse_time(record["started_at"])).total_seconds() // 60)
                penalized = FAILURES - {'ERROR'} - (set() if config.get('compilePenalty',False) else {'CE'})
                failures = sum(submission["verdict"] in penalized for submission in attempts[:attempts.index(accepted)])
                penalty += max(0, minutes) + config.get('wrongPenalty',20) * failures
            slots.append(slot)
        until = parse_time(record["finished_at"] or record["deadline"])
        elapsed = max(0, int((min(self._now(), until) - parse_time(record["started_at"])).total_seconds()))
        config = json.loads(record["config"] or "{}")
        return {"id": record["id"], "name": record["name"], "status": record["status"], "startedAt": record["started_at"], "deadline": record["deadline"], "finishedAt": record["finished_at"], "duration": record["duration"], "slots": slots, "accepted": sum(slot["accepted"] for slot in slots), "total": len(slots), "penalty": penalty, "elapsedSeconds": elapsed, "strategy": config.get("strategy", "comprehensive"), "constraints": config}

    def contest(self, identity):
        with self.lock:
            self._expire()
            return {"contest": self._contest(self._contest_record(identity)), "now": iso(self._now())}

    def finish_contest(self, identity):
        with self.lock:
            self._expire()
            record = self._contest_record(identity)
            if record["status"] == "running":
                with self._write() as connection:
                    self._finish_record(connection, record, iso(self._now()))
            return {"contest": self._contest(self._contest_record(identity)), "workspace": self.workspace()}

    def delete_contests(self, identity=None, all_records=False):
        if not isinstance(all_records, bool) or (not all_records and (not isinstance(identity, str) or not identity)):
            raise ServiceError(400, '请选择要删除的模拟赛记录')
        with self.lock:
            self._expire()
            if not all_records:
                record = self._contest_record(identity)
                if record['status'] == 'running':
                    raise ServiceError(409, '请先交卷，再删除这场模拟赛记录')
            # A tombstone preserves code and score evidence. Only entries
            # introduced by a deleted replay lose their active training link.
            removed = set()
            with self._write() as connection:
                rows = connection.execute("SELECT * FROM contests WHERE status='finished' AND deleted_at IS NULL" + ('' if all_records else ' AND id=?'), () if all_records else (identity,)).fetchall()
                connection.executemany('UPDATE contests SET deleted_at=? WHERE id=?', [(iso(self._now()), row['id']) for row in rows])
                remaining = {slot['id'] for other in connection.execute('SELECT slots FROM contests WHERE deleted_at IS NULL') for slot in json.loads(other['slots'])}
                practiced = {item for other in connection.execute('SELECT ids FROM practice_sets') for item in json.loads(other['ids'])}
                for record in rows:
                    if json.loads(record['config'] or '{}').get('strategy') != 'replay':
                        continue
                    for slot in json.loads(record['slots']):
                        ids = self._equivalent_ids(slot['id'])
                        if set(ids) & (remaining | practiced) or slot.get('trainingAdded') is False:
                            continue
                        placeholders = ','.join('?' for _ in ids)
                        if 'trainingAdded' not in slot:
                            # Legacy replay: preserve any evidence of training
                            # before the replay, or subsequent separate practice.
                            earlier = connection.execute(f'SELECT 1 FROM training WHERE id IN ({placeholders}) AND active_at<?', ids + [record['started_at']]).fetchone()
                            personal = connection.execute(f'SELECT 1 FROM drafts WHERE problem_id IN ({placeholders}) AND context=? AND code<>?', ids + ['', '']).fetchone()
                            external = connection.execute(f'SELECT 1 FROM submissions WHERE problem_id IN ({placeholders}) AND (contest_id IS NULL OR contest_id<>?)', ids + [record['id']]).fetchone()
                            if earlier or personal or external:
                                continue
                        pending = connection.execute(f'SELECT 1 FROM submissions WHERE problem_id IN ({placeholders}) AND finished_at IS NULL', ids).fetchone()
                        if pending:
                            continue
                        connection.execute(f'UPDATE training SET active=0,removed_at=?,mock_due=0,mock_due_at=NULL,mock_due_context=NULL WHERE id IN ({placeholders}) AND active=1', [iso(self._now())] + ids)
                        removed.add(slot['id'])
            return {'deleted': len(rows), 'removedTraining': len(removed), 'workspace': self.workspace()}

    def cancel_contest(self, identity):
        """Withdraw this arrangement without finishing or discarding real work."""
        if not isinstance(identity, str) or not identity or len(identity) > 512:
            raise ServiceError(400, '比赛编号无效')
        with self.lock, self._library_view():
            record = self.connection.execute('SELECT * FROM contests WHERE id=?', (identity,)).fetchone()
            if record is None:
                raise ServiceError(404, '没有找到这场模拟赛')
            if record['status'] == 'cancelled':
                return {'cancelled': True, 'workspace': self.workspace()}
            if record['status'] != 'running':
                raise ServiceError(409, '比赛已经结束，不能再取消')
            now = iso(self._now())
            with self._write() as connection:
                connection.execute("UPDATE contests SET status='cancelled',deleted_at=? WHERE id=?", (now, identity))
                referenced = {slot['id'] for other in connection.execute('SELECT slots FROM contests WHERE deleted_at IS NULL') for slot in json.loads(other['slots'])}
                referenced.update(item for other in connection.execute('SELECT ids FROM practice_sets') for item in json.loads(other['ids']))
                for slot in json.loads(record['slots']):
                    equivalents = self._equivalent_ids(slot['id'])
                    if set(equivalents) & referenced:
                        continue
                    previous = slot.get('trainingBefore')
                    if previous is not None:
                        connection.execute('UPDATE training SET active=?,active_at=?,removed_at=? WHERE id=?',
                                           (previous['active'],previous['active_at'],previous['removed_at'],slot['id']))
                    elif slot.get('trainingAdded'):
                        connection.execute('UPDATE training SET active=0,removed_at=? WHERE id=?', (now,slot['id']))
                    connection.execute('UPDATE training SET mock_due=0,mock_due_at=NULL,mock_due_context=NULL WHERE id=? AND mock_due_context=?', (slot['id'],identity))
            return {'cancelled': True, 'workspace': self.workspace()}

    def _completed_replay_contests(self):
        """Derive reveal eligibility from actual finished replays, including tombstones."""
        from contest_names import contest_name
        names = set()
        for record in self.connection.execute("SELECT config FROM contests WHERE status='finished'"):
            config = json.loads(record['config'] or '{}')
            original = config.get('contest')
            if config.get('strategy') == 'replay' and isinstance(original, str) and original.strip():
                names.add(contest_name(original))
        return sorted(names)

    def workspace(self):
        from copy import deepcopy
        with self.lock:
            signature = self._insights_signature(None)
            cached = getattr(self, '_workspace_cache', None)
            if signature is not None and cached and time.monotonic() - cached[0] < 3 and cached[1] == signature:
                result = deepcopy(cached[2])
                now = self._now()
                result['now'] = iso(now)
                for contest in result['contests']:
                    if contest['status'] == 'running':
                        contest['elapsedSeconds'] = max(0, int((min(now, parse_time(contest['deadline'])) - parse_time(contest['startedAt'])).total_seconds()))
                if result['activeContest']:
                    result['activeContest'] = next(item for item in result['contests'] if item['id'] == result['activeContest']['id'])
                return result
            result = self._build_workspace()
            signature = self._insights_signature(None)
            if signature is not None:
                self._workspace_cache = (time.monotonic(), signature, deepcopy(result))
            return result

    def _build_workspace(self):
        with self.lock, self._library_view():
            self._expire()
            review_plan = self.review_plan()
            review_tasks = {item['problemId']: item for item in review_plan['tasks']}
            from goals import Goals
            goal_overview = Goals(self).list(assign=True)
            goal_tasks = goal_overview.get('goalTasks', [])
            library = {row["id"]: row for row in self._library()}
            aliases = self._identity_map(list(library.values()))
            records = self.connection.execute("SELECT * FROM submissions WHERE mode='submit' ORDER BY submitted_at,rowid").fetchall()
            grouped = {}
            for submission in records:
                grouped.setdefault(aliases.get(submission["problem_id"], submission["problem_id"]), []).append(submission)
            running = self.connection.execute("SELECT * FROM contests WHERE status='running'").fetchone()
            locked = self._locked_ids(running) if running else set()
            now = self._now()
            today = now.astimezone(TRAINING_ZONE).date()
            # Keep the complete personal history; only the daily view is derived.
            activity = {}
            for event in self.connection.execute("SELECT problem_id,submitted_at AS at FROM submissions UNION ALL SELECT problem_id,saved_at AS at FROM drafts"):
                identity = aliases.get(event["problem_id"], event["problem_id"])
                activity[identity] = max(activity.get(identity, ""), event["at"])
            training = []
            for record in self.connection.execute("SELECT * FROM training WHERE active=1 ORDER BY active_at,id"):
                canonical = aliases.get(record["id"], record["id"])
                attempts = grouped.get(canonical, [])
                completed = [submission for submission in attempts if submission["finished_at"]]
                latest = completed[-1] if completed else None
                # 只有官方 AC 才算通过；record["accepted_at"] 由 _recompute_progress 保证已按官方口径清理。
                accepted_at = next((submission["submitted_at"] for submission in completed if submission["verdict"] == "AC" and submission["scope"] == "official"), record["accepted_at"])
                accepted = bool(accepted_at)
                queue = None
                if canonical not in locked:
                    if latest and latest["verdict"] in FAILURES or record["mock_due"]:
                        queue = "fill"
                    elif latest and latest["verdict"] == "SAMPLE_PASS" and not accepted:
                        queue = "verify"
                    if canonical in review_tasks:
                        queue = 'check' if review_tasks[canonical]['stage'] >= 2 else 'review'
                source = library.get(canonical)
                if source is None:
                    try:
                        source = self._row(record["id"])
                    except Exception as error:
                        if getattr(error, "status", None) != 404:
                            raise
                item = dict(source or {"id": record["id"], "title": record["id"], "contest": "", "problem": "", "difficulty": None, "tags": [], "knowledge": "", "platform": ""})
                last_attempt = attempts[-1] if attempts else None
                accepted_scope = ('official' if any(submission['scope']=='official' and submission['verdict']=='AC' for submission in completed) else 'local') if accepted else None
                item.update({"id": canonical, "accepted": accepted, "verdict": last_attempt["verdict"] if last_attempt else None, "scope": accepted_scope if accepted else last_attempt["scope"] if last_attempt else None, "attempts": len(attempts), "acceptedAt": accepted_at, "lastSubmittedAt": attempts[-1]["submitted_at"] if attempts else None, "queue": queue, "reviewCount": record["review_count"], "solutionSeen": bool(record["solution_pending"] or record["rewrite_due"]), "activeAt": record["active_at"]})
                last_activity = max(activity.get(canonical, ""), record["active_at"], record["solution_seen_at"] or "")
                item.update(lastActivityAt=last_activity, today=bool(queue or canonical in locked or parse_time(last_activity).astimezone(TRAINING_ZONE).date() == today))
                if canonical in review_tasks and canonical not in locked:
                    item['reviewTask'] = review_tasks[canonical]
                elif review_plan['reviewOnly'] and canonical not in locked:
                    item['today'] = bool(latest and parse_time(latest['submitted_at']).astimezone(TRAINING_ZONE).date() == today)
                    if not item['today']:
                        item['queue'] = None
                if canonical in locked:
                    item.update({"difficulty": None, "tags": [], "knowledge": ""})
                training.append(item)
            merged = {}
            for item in training:
                previous = merged.get(item["id"])
                if previous:
                    previous["queue"] = previous["queue"] or item["queue"]
                    previous["solutionSeen"] = previous["solutionSeen"] or item["solutionSeen"]
                    previous["reviewCount"] = max(previous["reviewCount"], item["reviewCount"])
                    previous["today"] = previous["today"] or item["today"]
                    previous["lastActivityAt"] = max(previous["lastActivityAt"], item["lastActivityAt"])
                else:
                    merged[item["id"]] = item
            training = list(merged.values())
            task_ids = {aliases.get(task['id'], task['id']) for task in goal_tasks}
            for task in goal_tasks:
                task['id'] = aliases.get(task['id'], task['id'])
            for item in training:
                if item['id'] in task_ids:
                    item['goalTask'] = True
                    item['today'] = True
            accepted_ids = {item["id"] for item in training if item["accepted"]}
            active_ids = {item["id"] for item in training}
            sets = []
            for record in self.connection.execute("SELECT * FROM practice_sets WHERE id NOT LIKE 'goal-contest:%' ORDER BY created_at DESC,id"):
                ids = list(dict.fromkeys(aliases.get(problem_id, problem_id) for problem_id in json.loads(record["ids"]) if aliases.get(problem_id, problem_id) in active_ids))
                if ids:
                    sets.append({"id": record["id"], "name": record["name"], "type": "practice", "ids": ids, "createdAt": record["created_at"], "accepted": len(set(ids) & accepted_ids), "total": len(set(ids))})
            contests = [self._contest(record) for record in self.connection.execute("SELECT * FROM contests WHERE deleted_at IS NULL ORDER BY started_at DESC,rowid DESC")]
            days = {parse_time(record["submitted_at"]).astimezone(TRAINING_ZONE).date() for record in records if record["finished_at"] and (record["code"].strip() or record["scope"]=="official")}
            day = now.astimezone(TRAINING_ZONE).date()
            if day not in days:
                day -= dt.timedelta(days=1)
            streak = 0
            while day in days:
                streak += 1
                day -= dt.timedelta(days=1)
            official_ac = [r for r in records if r['scope'] == 'official' and r['verdict'] == 'AC' and r['finished_at']]
            historical_ac = {aliases.get(r['problem_id'], r['problem_id']) for r in official_ac}
            today_ac = {aliases.get(r['problem_id'], r['problem_id']) for r in official_ac if parse_time(r['submitted_at']).astimezone(TRAINING_ZONE).date() == today}
            before_today_ac = {aliases.get(r['problem_id'], r['problem_id']) for r in official_ac if parse_time(r['submitted_at']).astimezone(TRAINING_ZONE).date() < today}
            pending = self.connection.execute("SELECT COUNT(*) FROM submissions WHERE finished_at IS NULL").fetchone()[0]
            return {"training": training, "sets": sets, "contests": contests, "completedReplayContests": self._completed_replay_contests(), "reviews": review_plan, "goals": goal_overview, "goalTasks": goal_tasks, "activeContest": next((contest for contest in contests if contest["status"] == "running"), None), "summary": {"todayAccepted": len(today_ac), "historicalAccepted": len(historical_ac), "beforeTodayAccepted": len(before_today_ac), "total": len(training), "accepted": sum(item["accepted"] for item in training), "samplePassed": sum(item["verdict"] == "SAMPLE_PASS" and not item["accepted"] for item in training), "attempts": len(records), "due": sum(item["queue"] is not None for item in training), "streak": streak, "pending": pending}, "now": iso(now)}

    def close(self):
        with self.lock:
            if self.closed:
                return
            self.closed = True
            for cancel in self.cancellations.values():
                cancel.set()
        self.executor.shutdown(wait=True, cancel_futures=False)
        self.leaderboard.close()
        if self.assets is not None and callable(getattr(self.assets, 'close', None)):
            self.assets.close()
        with self.lock:
            self.connection.close()
