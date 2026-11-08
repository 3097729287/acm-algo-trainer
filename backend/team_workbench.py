"""Shared-room workbench using isolated contest drafts and native OJ receipts.

The shared service owns membership, clocks, documents and edit leases. Local
contest mirrors reuse native statement/render/run/submit behavior; no peer's
acceptance is inserted into the account's personal submission history.
"""
from contextlib import contextmanager
from contextvars import ContextVar
import datetime as dt
import hashlib
import inspect
import json
import re
import threading
import time
import uuid
from team_training import relay, TeamServiceError
from training import ServiceError, iso, parse_time
from insights import canonical_url

_ACCESS = ContextVar('team_workbench_access', default=None)
_UUID = re.compile(r'[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}', re.I)
_WORKERS = threading.Lock()


def assert_authorized(training, contest_id):
    if _ACCESS.get() != (id(training), contest_id):
        raise TeamServiceError(403, 'TEAM_CONTROL_REQUIRED', '请在团队训练中取得编辑控制')


@contextmanager
def authorized(training, contest_id):
    token = _ACCESS.set((id(training), contest_id))
    try:
        yield
    finally:
        _ACCESS.reset(token)


def _error(code, message, status=409):
    raise TeamServiceError(status, 'TEAM_' + code, message)


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True)


def _sha(value):
    return hashlib.sha256(value.encode('utf8')).hexdigest()


def mirror(training, state, room_id, *, create=False):
    room = state.get('room')
    if not isinstance(room_id, str) or not _UUID.fullmatch(room_id) or not room or room.get('id') != room_id:
        _error('ROOM_CHANGED', '团队比赛已变更，请重新进入')
    profile = training._ranking_profile()
    if state.get('owner') != profile['user_id'] or room.get('teamId') != state.get('team', {}).get('id'):
        _error('OWNER_CHANGED', '账号已切换，请重新读取')
    if room.get('status') not in {'countdown', 'active', 'finished'}:
        _error('ROOM_INVALID', '团队比赛状态无效')
    start, end, now = room.get('startedAt'), room.get('deadline'), state.get('serverNow')
    if any(type(v) not in (int, float) or not (0 < v < 10**14) for v in (start, end, now)) or not 300000 <= end-start <= 18000000:
        _error('ROOM_INVALID', '团队比赛时间无效')
    problems = room.get('problems')
    if not isinstance(problems, list) or not 2 <= len(problems) <= 26 or len({p.get('id') for p in problems}) != len(problems):
        _error('ROOM_INVALID', '团队比赛题单无效')
    local_id = 'team-' + room_id
    slots = []
    for p in problems:
        if not isinstance(p.get('id'), str) or not 0 < len(p['id']) <= 512:
            _error('ROOM_INVALID', '团队题目编号无效')
        try:
            row = training._row(p['id'])
        except ServiceError as error:
            if error.status != 404:
                raise
            row = {}
        available = bool(p.get('available') and row and canonical_url(row.get('url')) == canonical_url(p.get('url')))
        slots.append({'id': p['id'], 'letter': p['letter'], 'title': p['title'], 'difficulty': row.get('difficulty'),
                      'tags': list(row.get('tags') or []), 'judgeScope': 'official' if available else 'unsupported',
                      'statementAvailable': available, 'trainingAdded': False})
    roster_hash = _sha(_json([{k: p[k] for k in ('id', 'url', 'letter')} for p in problems]))
    with training.lock:
        record = training.connection.execute('SELECT * FROM contests WHERE id=?', (local_id,)).fetchone()
        if record is None and not create:
            _error('NOT_ENTERED', '请先进入这场团队训练')
        if record is None and room['status'] == 'finished':
            _error('ROOM_FINISHED', '本场已结束，请查看团队历史')
        active = training.connection.execute("SELECT id FROM contests WHERE status='running' AND id!=?", (local_id,)).fetchone()
        if active and (not record or room['status'] != 'finished'):
            _error('CONTEST_ACTIVE', '请先结束当前比赛')
        if not any(s['statementAvailable'] for s in slots):
            _error('LIBRARY_OUTDATED', '本机尚无这场比赛的可用题面，请先更新题库')
        previous = json.loads(record['config']) if record else None
        if previous and any(previous.get(k) != v for k, v in {
                'teamRoomId': room_id, 'teamOwner': profile['user_id'], 'teamEndpoint': profile['endpoint'],
                'teamRosterSha256': roster_hash, 'serverStartedAt': start, 'serverDeadline': end}.items()):
            _error('ROOM_CHANGED', '团队比赛资料已变更，请重新读取')
        # Translate a trusted server duration into the local clock domain. The
        # original server instants remain frozen; scoring uses those instants.
        offset = training._now().timestamp()*1000 - now
        local_iso = lambda ms: iso(dt.datetime.fromtimestamp((ms+offset)/1000, dt.timezone.utc))
        config = previous or {'strategy': 'team', 'editedTrainingOnly': True, 'teamRoomId': room_id,
            'teamOwner': profile['user_id'], 'teamEndpoint': profile['endpoint'], 'teamRosterSha256': roster_hash,
            'serverStartedAt': start, 'serverDeadline': end}
        with training._write() as db:
            if record is None:
                db.execute("INSERT INTO contests(id,name,status,started_at,deadline,finished_at,duration,slots,config) VALUES(?,?,'running',?,?,NULL,?,?,?)",
                    (local_id, room['contestTitle'], local_iso(start), local_iso(end), round((end-start)/60000), _json(slots), _json(config)))
            elif room['status'] != 'finished':
                # Only a fresh server response may resume a prematurely expired
                # mirror after the system clock changes. Existing facts stay put.
                db.execute("UPDATE contests SET status='running',started_at=?,deadline=?,finished_at=NULL WHERE id=?",
                           (local_iso(start), local_iso(end), local_id))
            if room['status'] == 'finished':
                record = db.execute('SELECT * FROM contests WHERE id=?', (local_id,)).fetchone()
                training._finish_record(db, record, local_iso(room.get('finishedAt') or end))
        return training._contest(training._contest_record(local_id))


def refresh_existing(training, state):
    recover_receipts(training)
    with training.lock:
        pending=training.connection.execute("SELECT COUNT(*) FROM account_preferences WHERE key LIKE 'team-native:%' AND json_valid(value) AND json_extract(value,'$.phase')='receipt-ready'").fetchone()[0]
    state['pendingNativeReceipts']=pending
    if pending:queue_receipts(training)
    room = state.get('room')
    if room and isinstance(room.get('id'), str):
        with training.lock:
            exists = training.connection.execute('SELECT 1 FROM contests WHERE id=?', ('team-'+room['id'],)).fetchone()
        if exists:
            return mirror(training, state, room['id'])
    return None


def _current(training, body, *, create=False):
    state = relay(training)
    contest = mirror(training, state, body.get('roomId'), create=create)
    return state, contest


def read(server, action, query):
    if action != 'problem' or set(query)-{'id', 'roomId', 'background', 'refresh'} or any(len(v) != 1 for v in query.values()):
        _error('REQUEST_INVALID', '团队训练请求无效', 400)
    body = {k: v[0] for k, v in query.items()}
    state, contest = _current(server.training, body)
    state['localContest'] = contest
    room, training = state['room'], server.training
    if body.get('id') != room['problemId']:
        _error('DOCUMENT_CHANGED', '队伍已切换题目，请重新读取')
    answer = training.problem(body['id'], contest['id'], background=True, refresh=body.get('refresh') == '1')
    document = room['document']
    answer.update(draft=document['code'], draftLanguage=document['language'],
                  draftSavedAt=iso(dt.datetime.fromtimestamp(document['savedAt']/1000, dt.timezone.utc)) if document.get('savedAt') else None,
                  sharedDocumentRevision=document['revision'], formattingAvailable=False, sharedState=state)
    return answer


def write(server, action, body):
    training = server.training
    allowed = {
        'enter': {'roomId'},
        'draft': {'requestId', 'roomId', 'leaseToken', 'id', 'revision', 'language', 'code'},
        'run': {'requestId', 'roomId', 'leaseToken', 'id', 'revision', 'language', 'code', 'input', 'sampleRun'},
        'official-open': {'requestId', 'roomId', 'leaseToken', 'id', 'revision', 'language', 'code'},
        'official-submit': {'requestId', 'roomId', 'leaseToken', 'id', 'revision', 'language', 'code'},
        'translate': {'roomId', 'id'},
    }
    if action not in allowed or not isinstance(body, dict) or set(body)-allowed[action]:
        _error('REQUEST_INVALID', '团队训练请求无效', 400)
    if action == 'enter':
        state, contest = _current(training, body, create=True)
        return {**state, 'localContest': contest}
    if action == 'draft':
        remote = {k: v for k, v in body.items() if k != 'id'}
        remote['problemId'] = body.get('id')
        state = relay(training, 'draft', remote)
        contest = mirror(training, state, body.get('roomId'))
        state['localContest'] = contest
        try:
            with authorized(training, contest['id']):
                training.save_draft(body['id'], body['code'], contest['id'], body['language'])
        except ServiceError:
            # The remote CAS is already durable. An ended local mirror must
            # not turn a confirmed shared save into an ambiguous retry.
            pass
        return {'savedAt': iso(dt.datetime.fromtimestamp(state['room']['document']['savedAt']/1000, dt.timezone.utc)),
                'sharedState': state, 'documentRevision': state['ack']['documentRevision']}
    if action == 'translate':
        state, contest = _current(training, body)
        if body.get('id') != state['room']['problemId']:
            _error('DOCUMENT_CHANGED', '队伍已切换题目')
        return server.translate_problem(body['id'], contest['id'])
    code = training._code(body.get('code'))
    language = training._language(body.get('language', 'cpp17'))
    purpose = 'run' if action == 'run' else 'submit' if action == 'official-submit' else 'open'
    if purpose != 'run' and isinstance(body.get('requestId'), str) and _UUID.fullmatch(body['requestId']):
        with training.lock:
            previous = training.connection.execute('SELECT value FROM account_preferences WHERE key=?', ('team-native:'+body['requestId'],)).fetchone()
            if previous:
                journal = json.loads(previous['value']);grant = journal['authorization'];profile = training._ranking_profile()
                if journal.get('owner') != profile['user_id'] or journal.get('endpoint') != profile['endpoint'] or any(
                        grant.get(k) != v for k,v in {'roomId':body.get('roomId'),'problemId':body.get('id'),
                        'revision':body.get('revision'),'language':language,'purpose':purpose,'inputSha256':_sha(code)}.items()):
                    _error('REQUEST_CONFLICT', '该提交编号已用于另一份代码')
                if journal.get('sessionId'):
                    return {'sessionId':journal['sessionId'],'status':'unconfirmed','url':grant['url']}
                _error('SUBMISSION_UNCERTAIN', '本次提交状态尚未确认，请先查看原站记录')
    before = time.monotonic()
    state = relay(training, 'authorize', {'requestId': body.get('requestId'), 'roomId': body.get('roomId'),
        'leaseToken': body.get('leaseToken'), 'problemId': body.get('id'), 'revision': body.get('revision'),
        'language': language, 'purpose': purpose, 'inputSha256': _sha(code)})
    grant = (state.get('ack') or {}).get('authorization') or {}
    if any(grant.get(k) != v for k, v in {'id': body.get('requestId'), 'roomId': body.get('roomId'),
            'problemId': body.get('id'), 'revision': body.get('revision'), 'language': language,
            'purpose': purpose, 'inputSha256': _sha(code)}.items()):
        _error('AUTHORIZATION_INVALID', '共享代码授权无效')
    if grant.get('expiresAt', 0) <= state['serverNow'] + (time.monotonic()-before)*1000:
        _error('AUTHORIZATION_EXPIRED', '编辑授权已过期，请重新读取')
    contest = mirror(training, state, body.get('roomId'))
    if action == 'run':
        with authorized(training, contest['id']):
            return training.submit(body['id'], code, mode='run', input_text=body.get('input', ''),
                                   contest_id=contest['id'], sample_run=body.get('sampleRun'), language=language)
    opener = server.official_submitter if purpose == 'submit' else server.official_opener
    if not callable(opener):
        _error('BROWSER_UNAVAILABLE', '请在 ToBe 桌面版连接浏览器提交', 503)
    supports_language = 'language' in inspect.signature(opener).parameters
    if language != 'cpp17' and not supports_language:
        _error('LANGUAGE_UNSUPPORTED', '当前浏览器连接不支持 Python 3', 422)
    key = 'team-native:' + grant['id']
    with training.lock:
        prior = training.connection.execute('SELECT value FROM account_preferences WHERE key=?', (key,)).fetchone()
        if prior:
            journal = json.loads(prior['value'])
            if journal.get('sessionId'):
                return {'sessionId': journal['sessionId'], 'status': 'unconfirmed', 'url': grant['url']}
            _error('SUBMISSION_UNCERTAIN', '本次提交状态尚未确认，请先查看原站记录')
        row = training._row(body['id'])
        if canonical_url(row.get('url')) != canonical_url(grant.get('url')):
            _error('PROBLEM_CHANGED', '本机原题链接与队伍题目不符')
        preparation = getattr(server, 'browser_preparation', None)
        if purpose == 'submit' and preparation is not None:
            preparation.check_submission(grant['url'])
        with authorized(training, contest['id']):
            training.assert_official_allowed(body['id'], contest['id'])
        journal = {'owner': state['owner'], 'endpoint': training._ranking_profile()['endpoint'],
                   'authorization': grant, 'phase': 'starting', 'contestId': contest['id'],
                   'localStartedAt':iso(training._now()), 'handle':_bound_handle(training,grant['url'])}
        with training._write() as db:
            db.execute('INSERT INTO account_preferences(key,value,updated_at) VALUES(?,?,?)', (key, _json(journal), iso(training._now())))
        with authorized(training, contest['id']):
            if supports_language:
                opened = opener(grant['url'], code, row['title'], language=language)
            else:
                opened = opener(grant['url'], code, row['title'])
        result = opened if isinstance(opened, dict) else {'sessionId': opened, 'status': 'opened', 'url': grant['url']}
        if not isinstance(result.get('sessionId'), str) or not result['sessionId']:
            _error('SUBMISSION_UNCERTAIN', '浏览器未返回可核对的提交会话', 503)
        journal.update(sessionId=result['sessionId'], phase='opened')
        with training._write() as db:
            db.execute('UPDATE account_preferences SET value=?,updated_at=? WHERE key=?', (_json(journal), iso(training._now()), key))
    server.register_official_session(result['sessionId'], {'id': body['id'], 'contestId': contest['id'],
        'url': grant['url'], 'code': code, 'language': language, 'teamIntentId': grant['id']}, result)
    return result


def record_receipt(training, submission, session, receipt):
    """Journal only an actual persisted official record, never a UI verdict."""
    identity = session.get('teamIntentId')
    if not isinstance(submission, dict):
        return
    from submission_evidence import verified_receipt
    with training.lock:
        if not isinstance(identity,str) or not _UUID.fullmatch(identity):
            session_id=session.get('sessionId')
            if not isinstance(session_id,str):return
            restored=training.connection.execute("SELECT key FROM account_preferences WHERE key LIKE 'team-native:%' AND json_valid(value) AND json_extract(value,'$.sessionId')=? LIMIT 2",(session_id,)).fetchall()
            if len(restored)!=1:return
            identity=restored[0]['key'].split(':',1)[1]
        stored = training.connection.execute('SELECT * FROM submissions WHERE id=?', (submission.get('id'),)).fetchone()
        pending = training.connection.execute('SELECT value FROM account_preferences WHERE key=?', ('team-native:'+identity,)).fetchone()
        if not stored or not pending or not verified_receipt(dict(stored)):
            return
        journal = json.loads(pending['value']);grant = journal['authorization']
        if stored['problem_id'] != grant['problemId'] or _sha(stored['code']) != grant['inputSha256']:
            return
        if journal.get('phase')=='confirmed' and journal.get('localSubmissionId')==stored['id']:
            return
        remote = re.match(r'^原站确认提交 #([1-9][0-9]*)', stored['message'])
        journal.update(phase='receipt-ready', submissionId=remote[1], localSubmissionId=stored['id'],
                       submittedAt=stored['submitted_at'], finishedAt=stored['finished_at'])
        if not journal.get('handle'):journal['handle']=_bound_handle(training,grant['url'])
        with training._write() as db:
            db.execute('UPDATE account_preferences SET value=?,updated_at=? WHERE key=?',
                       (_json(journal), iso(training._now()), 'team-native:'+identity))
    queue_receipts(training)


def _bound_handle(training,url):
    from urllib.parse import urlsplit
    key={'codeforces.com':'codeforces','atcoder.jp':'atcoder','ac.nowcoder.com':'nowcoder'}.get((urlsplit(url).hostname or '').removeprefix('www.'))
    extensions=getattr(training.store,'extensions',None)
    if key and extensions is not None:
        try:
            value=extensions.snapshot().get('settings',{}).get('accounts',{}).get(key)
            return value.strip() if isinstance(value,str) else ''
        except (OSError,ValueError,RuntimeError,ServiceError):pass
    return ''


def recover_receipts(training):
    """Reconnect a lost browser callback only to a unique persisted owner fact.

    A crash between starting the browser and saving its session never causes a
    second submission. Public sync records without the exact private source,
    another contest, older records and ambiguous identical attempts stay pending.
    """
    from submission_evidence import verified_receipt
    with training.lock:
        if training.closed:return
        profile=training._ranking_profile()
        rows=training.connection.execute("SELECT key,value FROM account_preferences WHERE key LIKE 'team-native:%' AND json_valid(value)").fetchall()
        journals=[(row['key'],value) for row in rows if isinstance(value:=json.loads(row['value']),dict)]
        used={value.get('localSubmissionId') for _,value in journals if value.get('localSubmissionId')}
        matches=[];counts={}
        for key,journal in journals:
            if journal.get('phase') not in {'starting','opened'} or journal.get('owner')!=profile['user_id'] or journal.get('endpoint')!=profile['endpoint']:continue
            grant=journal.get('authorization') or {}
            if not isinstance(grant,dict):continue
            intent=grant.get('id')
            if not isinstance(intent,str) or not _UUID.fullmatch(intent) or key!='team-native:'+intent:continue
            try:started=parse_time(journal.get('localStartedAt'))
            except (ValueError,TypeError,AttributeError):continue
            if not started:continue
            candidates=[]
            for row in training.connection.execute("SELECT * FROM submissions WHERE contest_id=? AND problem_id=? AND scope='official' AND mode='submit' AND finished_at IS NOT NULL",(journal.get('contestId'),grant.get('problemId'))):
                saved=dict(row)
                if saved['id'] in used or not verified_receipt(saved) or _sha(saved['code'])!=grant.get('inputSha256'):continue
                if parse_time(saved['submitted_at'])>=started:candidates.append(saved)
            for saved in candidates:counts[saved['id']]=counts.get(saved['id'],0)+1
            if len(candidates)==1:matches.append((intent,candidates[0]))
        for intent,row in matches:
            if counts[row['id']]==1:
                record_receipt(training,row,{'teamIntentId':intent},{})


def deliver_receipts(training):
    """Drain exact durable OJ facts; no remote verdict is supplied by the UI."""
    with training.lock:
        if training.closed:return
        profile=training._ranking_profile()
        rows=training.connection.execute("SELECT key,value FROM account_preferences WHERE key LIKE 'team-native:%' AND json_valid(value) AND json_extract(value,'$.phase')='receipt-ready' ORDER BY updated_at LIMIT 20").fetchall()
    for row in rows:
        journal=json.loads(row['value'])
        if journal.get('owner')!=profile['user_id'] or journal.get('endpoint')!=profile['endpoint']:continue
        grant=journal.get('authorization') or {};intent=grant.get('id')
        if not isinstance(intent,str) or not _UUID.fullmatch(intent):continue
        handle=journal.get('handle') or _bound_handle(training,grant.get('url',''))
        if not handle:continue
        with training.lock:
            if training.closed:return
            stored=training.connection.execute('SELECT * FROM submissions WHERE id=?',(journal.get('localSubmissionId'),)).fetchone()
            from submission_evidence import verified_receipt
            if not stored or not verified_receipt(dict(stored)) or stored['problem_id']!=grant.get('problemId') or _sha(stored['code'])!=grant.get('inputSha256'):continue
        request_id=str(uuid.UUID(_sha('team-native-receipt:'+intent)[:32],version=4))
        try:
            answer=relay(training,'native-receipt',{'requestId':request_id,'intentId':intent,
                'submissionId':journal['submissionId'],'handle':handle},internal=True)
        except ServiceError:
            continue
        receipt=answer.get('receipt') or {}
        if receipt.get('intentId')!=intent or receipt.get('status')!='confirmed' or receipt.get('submissionId')!=journal['submissionId']:continue
        if receipt.get('verdict') not in {'AC','WA','TLE','MLE','RE','CE','OLE'}:continue
        with training.lock:
            if training.closed:return
            current_profile=training._ranking_profile()
            if any(current_profile.get(k)!=profile.get(k) for k in ('user_id','endpoint','auth_token')):return
            current=training.connection.execute('SELECT value FROM account_preferences WHERE key=?',(row['key'],)).fetchone()
            if not current:continue
            value=json.loads(current['value'])
            if value.get('phase')!='receipt-ready' or value.get('localSubmissionId')!=journal['localSubmissionId']:continue
            value.update(phase='confirmed',verifiedReceipt=receipt,handle=handle)
            with training._write() as db:
                db.execute('UPDATE account_preferences SET value=?,updated_at=? WHERE key=?',(_json(value),iso(training._now()),row['key']))


def queue_receipts(training):
    """Bounded background retry; public source delays never block the editor."""
    with _WORKERS:
        worker=getattr(training,'_team_receipt_delivery',None)
        if worker and (worker['running'] or time.monotonic()-worker['at']<15):return
        if training.closed:return
        worker={'running':True,'at':time.monotonic()};training._team_receipt_delivery=worker
    def run():
        try:deliver_receipts(training)
        except (OSError,ValueError,RuntimeError):pass
        finally:
            with _WORKERS:worker['running']=False
    threading.Thread(target=run,name='tb-team-receipts',daemon=True).start()
