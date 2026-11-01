"""Backend-only source-presence evidence; never hydrate historical code."""
import json
import re
from progression import parse_time


def matching_contest(record, contests):
    """Match an exact saved problem and submission instant, never its title."""
    stamp=parse_time(record.get('submitted_at'))
    if not stamp:return None
    candidates=[]
    for contest in contests:
        if contest.get('status') not in ('running','finished'):continue
        start=parse_time(contest.get('started_at'));end=parse_time(contest.get('deadline'))
        finish=parse_time(contest.get('finished_at'))
        if finish and end:end=min(end,finish)
        if not start or not end or not start<=stamp<=end:continue
        try:slots=json.loads(contest['slots']) if isinstance(contest.get('slots'),str) else contest.get('slots',[])
        except (ValueError,TypeError):continue
        if not isinstance(slots,list) or not any(isinstance(slot,dict) and slot.get('id')==record.get('problem_id') for slot in slots):continue
        candidates.append(contest['id'])
    existing=record.get('contest_id')
    if existing:return existing if existing in candidates else None
    return candidates[0] if len(candidates)==1 else None


def verified_receipt(record):
    return (record.get('mode')=='submit' and record.get('scope')=='official'
            and bool(re.fullmatch(r'official-[0-9a-f]{64}',str(record.get('id') or '')))
            and bool(re.match(r'^原站确认提交 #[1-9][0-9]*(?:\s|$)',str(record.get('message') or '')))
            and bool(parse_time(record.get('submitted_at'))) and bool(parse_time(record.get('finished_at'))))

def source_present(record):
    if record.get('sourcePresent') is True: return True
    code = record.get('code')
    if not isinstance(code, str) or not code.strip(): return False
    if code.startswith('\x00TB-CODE-V2:'):
        from account_chunks import code_reference
        from training import ServiceError
        try:
            reference = code_reference(code)
            return bool(reference and reference['bytes'] > 0)
        except ServiceError:
            return False
    return True


def annotate_sources(records, connection):
    """Derive the flag from SQLite, discarding any caller-supplied annotation.

    A private, validated code-reference row proves source was saved even when a
    new device has not downloaded its immutable historical archive. Public
    receipts need a private source reference or a stored owner receipt within
    a verified original contest / saved mock window; ordinary public receipts
    remain unqualified.
    """
    rows = [{key: value for key, value in dict(record).items() if key not in {'sourcePresent','ownerReceipt','timedReceipt'}} for record in records]
    tables={row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    # Owner-scoped official receipts are durable even when the original site
    # does not expose their source. Derive provenance from stored rows, never
    # accept an annotation supplied by a caller or a public-history object.
    if 'submissions' in tables:
        fields=('id','problem_id','contest_id','mode','scope','verdict','submitted_at','finished_at','solution_seen','message')
        columns={row[1] for row in connection.execute('PRAGMA table_info(submissions)')}
        if set(fields)<=columns:
            by_id={row.get('id'):row for row in rows}
            contests=[]
            if 'contests' in tables:
                cols=('id','status','started_at','deadline','finished_at','slots')
                if set(cols)<={r[1] for r in connection.execute('PRAGMA table_info(contests)')}:
                    contests=[dict(zip(cols,r)) for r in connection.execute('SELECT '+','.join(cols)+' FROM contests')]
            for stored in connection.execute('SELECT '+','.join(fields)+' FROM submissions WHERE scope=\'official\''):
                saved=dict(zip(fields,stored));row=by_id.get(saved['id'])
                if row is None or not verified_receipt(saved) or any(row.get(key)!=saved[key] for key in fields):continue
                row['ownerReceipt']=True
                row['timedReceipt']=bool(matching_contest(saved,contests))
    pending = {row.get('id'): row for row in rows if not source_present(row) and row.get('id')}
    if pending and connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='account_sync_code_refs'").fetchone():
        from account_chunks import code_reference
        from training import ServiceError
        for identity, encoded in connection.execute('SELECT submission_id,reference FROM account_sync_code_refs'):
            if identity not in pending: continue
            try:
                reference = code_reference(encoded)
                if reference and reference['bytes'] > 0: pending[identity]['sourcePresent'] = True
            except ServiceError:
                continue
    return rows
