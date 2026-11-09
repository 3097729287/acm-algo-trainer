"""Replay the exact public 12-slot roster with isolated generated user history.

The supplied release database is opened read-only. Only its 13 public records
and referenced public resources enter a fresh small fixture. No real account,
browser, submission, program installation or source database is changed.
"""
import argparse
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common')]
from assets import AssetLibrary
from catalog_identity import unique_catalog_rows
from library import LibraryDatabase
from question_identity import PAIR_IDS, PAIR_KEY, PAIR_KEYS, question_key
from statement_asset_store import references
from statement_integrity import content_complete
from training import TrainingService, UTC


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify(source):
    source = source.resolve()
    before = (source.stat().st_size, source.stat().st_mtime_ns)
    original = LibraryDatabase(source, readonly=True)
    identities = [f'remote:codeforces:105139::{letter}' for letter in 'ABCDEFGHIJKL']
    identities.insert(0, PAIR_IDS[0])
    with original.connection() as db:
        records = [dict(db.execute('SELECT * FROM problems WHERE id=?', (identity,)).fetchone()) for identity in identities]
        statements = {identity: json.loads(db.execute('SELECT content FROM statements WHERE problem_id=?', (identity,)).fetchone()[0])
                      for identity in identities}
        source_native_urls = {row['url']: row['id'] for row in db.execute('SELECT p.url,p.id FROM problems p WHERE p.id IN (?,?)', PAIR_IDS)}
        needed = set().union(*(references(value) for value in statements.values()))
        assets = [tuple(db.execute('SELECT sha256,mime,data FROM statement_assets WHERE sha256=?', (digest,)).fetchone())
                  for digest in sorted(needed)]
    assert len(records) == 13 and all(content_complete(value) for value in statements.values())
    assert len(source_native_urls) == 2
    clock = [dt.datetime(2026, 11, 9, 4, tzinfo=UTC)]
    with tempfile.TemporaryDirectory(prefix='tb-verified-hubei-identity-') as folder:
        directory = Path(folder)
        library = LibraryDatabase(directory / 'public.sqlite3')
        with library.connection() as db:
            db.executemany('INSERT INTO problems VALUES(?,?,?,?)',
                           [(r['id'], r['url'], r['raw'], r['encoded']) for r in records])
            db.executemany('INSERT INTO statements VALUES(?,?)',
                           [(identity, json.dumps(value, ensure_ascii=False)) for identity, value in statements.items()])
            db.executemany('INSERT INTO statement_assets VALUES(?,?,?)', assets)
            library._rebuild_urls(db)
        class Store:
            data_root = directory
            extensions = None
            def __init__(self):
                self.library = library
            def data(self):
                return {'rows': unique_catalog_rows([json.loads(row['encoded']) for row in records])}
            def raw_rows(self):
                return [json.loads(row['raw']) for row in records]
            def row(self, identity):
                return library.find(identity)['raw']
            def encode_row(self, raw, _today=None):
                return library.find(raw['_id'])['encoded']
        store = Store()
        assets = AssetLibrary(store, directory / 'assets')
        hub = {'accounts': [{'platform': 'Luogu', 'solved': [
            {'url': PAIR_KEYS[0], 'acceptedAt': '2026-10-01T04:00:00Z'},
            {'url': PAIR_KEYS[1], 'acceptedAt': '2026-11-01T04:00:00Z'}]}]}
        class Extensions:
            def snapshot(self):
                return copy.deepcopy(hub)
            def rows(self):
                return []
            def row(self, identity):
                value = library.find(identity)
                return value['raw'] if value else None
        store.extensions = Extensions()
        with patch('leaderboard.LeaderboardClient.queue_sync', return_value=None), patch.dict('os.environ', {'TB_OFFLINE': '1'}):
            service = TrainingService(store, directory / 'generated-history.sqlite3', assets=assets,
                                      clock=lambda: clock[0], backup_dir=directory / 'backups',
                                      account_provider=lambda _owner: None)
            try:
                service.connection.execute("INSERT INTO submissions(id,problem_id,mode,code,submitted_at,finished_at,verdict,scope,solution_seen) VALUES('old-lg',?,'submit','kept historical code','2026-10-01T04:00:00Z','2026-10-01T04:00:00Z','AC','official',0)", (PAIR_IDS[0],))
                service.connection.execute('INSERT INTO official_first_xp_awards VALUES(?,?,?)',
                                           (PAIR_KEYS[0], '2026-10-01T04:00:00Z', 200))
                service.save_draft(PAIR_IDS[0], 'kept LG draft')
                service.save_draft(PAIR_IDS[1], 'kept CF H draft')
                old_receipt = tuple(service.connection.execute("SELECT * FROM submissions WHERE id='old-lg'").fetchone())
                old_awards = list(map(tuple, service.connection.execute('SELECT * FROM official_first_xp_awards')))
                old_drafts = list(map(tuple, service.connection.execute('SELECT * FROM drafts ORDER BY problem_id')))
                old_hub = copy.deepcopy(hub)
                native_map = service._identity_map(store.data()['rows'])
                assert native_map[PAIR_IDS[0]] == PAIR_IDS[0] and native_map[PAIR_IDS[1]] == PAIR_IDS[1]
                assert [library.find(url=url)['id'] for url in source_native_urls] == list(source_native_urls.values())
                catalogue = store.data()['rows']
                assert len(catalogue) == 13 and len({question_key(row.get('url')) or row['id'] for row in catalogue}) == 12
                assert len([r for r in catalogue if r.get('questionKey') == PAIR_KEY]) == 2
                solved = service._solved_problem_keys(catalogue)
                options = {'excludeSolved': True, 'platform': '', 'tags': [], 'reviewedOnly': False}
                assert all(not service._eligible_contest_row(row, options, 0, 4000, solved)
                           for row in catalogue if row['id'] in PAIR_IDS)
                eligible = [row for row in assets.candidates(catalogue)
                            if service._eligible_contest_row(row, options, 0, 4000, solved)]
                assert len(eligible) == 11
                # The existing comprehensive rule requires distinct ascending
                # ratings. These eleven tasks have ten distinct rating bands.
                new_paper = service.preview_contest({'count': 10, 'min': 0, 'max': 4000, 'excludeSolved': True})['plan']
                assert len(new_paper['slots']) == 10 and not set(PAIR_IDS) & {s['id'] for s in new_paper['slots']}
                contest_name = next(row['contest'] for row in catalogue if row['id'] == PAIR_IDS[1])
                plan = service.preview_replay({'contest': contest_name})['plan']
                assert plan['event']['complete'] and plan['event']['availableCount'] == 12
                assert [slot['letter'] for slot in plan['slots']] == list('ABCDEFGHIJKL')
                assert plan['slots'][7]['id'] == PAIR_IDS[1]
                contest = service.start_contest({'ids': [slot['id'] for slot in plan['slots']],
                                                 'duration': plan['duration'], 'previewId': plan['previewId']})['contest']
                assert contest['total'] == 12 and contest['accepted'] == 0
                locked = service._locked_ids(service._contest_record(contest['id']))
                assert set(PAIR_IDS) <= locked
                problem = service.problem(PAIR_IDS[1], contest['id'])
                assert problem['url'] == 'https://codeforces.com/gym/105139/problem/H'
                assert problem['statementAvailable'] and problem['samples'] == statements[PAIR_IDS[1]]['samples']
                clock[0] += dt.timedelta(minutes=5)
                receipt = service.record_official({'id': PAIR_IDS[1], 'contestId': contest['id'],
                    'code': 'new contest source', 'url': problem['url']},
                    {'status': 'finished', 'verdict': 'AC', 'submissionId': '99999991', 'acceptedAt': clock[0].isoformat()})
                assert receipt['contestId'] == contest['id'] and receipt['scope'] == 'official'
                current = service.contest(contest['id'])['contest']
                assert current['total'] == 12 and current['accepted'] == 1
                assert current['slots'][7]['id'] == PAIR_IDS[1]
                records_now = [dict(row) for row in service.connection.execute('SELECT * FROM submissions')]
                assert service._first_acceptance_xp(catalogue, records_now) == 200
                assert list(map(tuple, service.connection.execute('SELECT * FROM official_first_xp_awards'))) == old_awards
                assert tuple(service.connection.execute("SELECT * FROM submissions WHERE id='old-lg'").fetchone()) == old_receipt
                assert list(map(tuple, service.connection.execute('SELECT * FROM drafts ORDER BY problem_id'))) == old_drafts
                assert store.extensions.snapshot() == old_hub
                all_evidence = service._evidence(hub=hub)
                daily = service._evidence('2026-11-09', hub=hub)
                assert len(all_evidence) == 1 and all_evidence[0]['day'] == '2026-10-01'
                assert len(daily) == 1 and daily[0]['newProblem'] is False
                insight = service.insights(hub)
                assert insight['summary']['officialSolved'] == insight['summary']['totalSolved'] == 1
                result = {'publicRowsReadOnly': 13, 'publicAssetsCopied': len(needed),
                          'publicFixtureDatabaseBytes': library.path.stat().st_size,
                          'questionCount': 12, 'nativeEntrancesPreserved': 13,
                          'fullHubeiRoster': 12, 'unsolvedCandidateQuestions': 11, 'generatedUnsolvedPaper': 10,
                          'hNativeId': PAIR_IDS[1], 'hNativeUrl': problem['url'],
                          'oldGlobalFirstDay': all_evidence[0]['day'], 'todayNewProblem': False,
                          'newContestAcceptedSlots': current['accepted'], 'firstXpPreserved': 200,
                          'newFirstXpAwardRows': 0, 'oldSourceDraftReceiptAwardRowsUnchanged': True,
                          'oldCachedTwoUrlKeysUnchanged': True, 'livePersonalDatabasesOpened': 0,
                          'publicOriginalStatementSha256': {key: sha(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()) for key, value in statements.items()}}
            finally:
                service.close()
                assets.close()
    assert (source.stat().st_size, source.stat().st_mtime_ns) == before
    result.update(sourceDatabaseOpenedReadOnly=True, sourceDatabaseBytes=before[0],
                  sourceDatabaseStatUnchanged=True, isolatedFixtureRemoved=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--record', type=Path)
    args = parser.parse_args()
    result = verify(args.source)
    if args.record:
        args.record.parent.mkdir(parents=True, exist_ok=True)
        args.record.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8', newline='\n')
    print(json.dumps(result, ensure_ascii=True))
