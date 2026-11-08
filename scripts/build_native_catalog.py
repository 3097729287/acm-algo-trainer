"""Compile the existing public catalogue into an indexed, immutable native view.

This is a build-time content compiler, never a runtime Python fallback. The
public SQLite seed stays read-only; no private workspace or credentials are used.
"""
from pathlib import Path
import ast
import hashlib
import json
import os
import sqlite3
import sys
import threading
import zlib
from contextlib import closing
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
os.environ['TB_OFFLINE'] = '1'
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/common')]


def public_store(seed):
    from store import Store
    from library import LibraryDatabase
    from contestmeta import ContestDates
    value = Store.__new__(Store)
    value.library = LibraryDatabase(seed, readonly=True)
    value.lock = threading.RLock()
    value._identity_lock = threading.RLock()
    value._identity_snapshot = None
    value.extensions = None
    value.data_root = str(ROOT / '.backups/native-public-input')
    value.contest_dates = ContestDates(value)
    value._refresh_training_membership()
    return value


def signature(seed):
    with closing(sqlite3.connect(seed.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        schema = db.execute("SELECT value FROM library_meta WHERE key='schema'").fetchone()[0]
        revision = db.execute("SELECT value FROM library_meta WHERE key='revision'").fetchone()[0]
        generation = db.execute('SELECT identity,generation FROM catalog_generation WHERE id=1').fetchone()
        counts = {name: db.execute(f'SELECT count(*) FROM {name}').fetchone()[0]
                  for name in ['problems', 'statements', 'solutions', 'lectures', 'training_lists']}
    return {'schema': schema, 'revision': revision, 'generation': list(generation), 'counts': counts}


def patch_values(before, after, path=()):
    if isinstance(before, dict) and isinstance(after, dict):
        for key in before.keys() - after.keys():
            yield {'path': [*path, key], 'remove': True}
        for key, value in after.items():
            if key not in before:
                yield {'path': [*path, key], 'value': value}
            else:
                yield from patch_values(before[key], value, (*path, key))
    elif before != after:
        yield {'path': list(path), 'value': after}


def public_replay_events(store,assets,rows):
    """Compile the current public roster logic without an account journal."""
    from training import TrainingService
    projection=SimpleNamespace(lock=store.lock,_library=lambda:rows,
        _contest_candidates=lambda group,official=False:assets.candidates(group,official=official))
    return TrainingService.replay_events(projection)


def build(destination=None):
    from catalog_payload import project_row
    from catalog_identity import remote_aliases
    from insights import canonical_url
    import status_report
    import lecture_library
    from assets import AssetLibrary
    from knowledge import enrich_row
    from statement_asset_store import dehydrate
    seed = ROOT / 'data/library.sqlite3'
    destination = destination or ROOT / 'data/native-catalog.sqlite3'
    staging = destination.with_suffix('.building.sqlite3')
    if staging.exists():
        raise RuntimeError(f'Incomplete previous content build is preserved: {staging}')
    before = signature(seed)
    store = public_store(seed)
    rows = store._catalog_rows()
    revision = hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    aliases = {}
    for row in rows:
        aliases[row['id']] = row['id']
        for alias in [*row.get('aliasIds', []), *remote_aliases(row)]:
            aliases[alias] = row['id']
    # Preserve every legacy ID, including duplicate originals hidden by dedup.
    urls = {canonical_url(row.get('url')): row['id'] for row in rows if canonical_url(row.get('url'))}
    for row in store.library.identity_rows():
        canonical = urls.get(canonical_url(row.get('url')))
        if canonical:
            aliases[row['id']] = canonical
    dump = lambda value: json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    with sqlite3.connect(staging) as db:
        db.executescript('''
          CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
          CREATE TABLE catalogue(id TEXT PRIMARY KEY,position INTEGER NOT NULL,full BLOB NOT NULL,compact TEXT NOT NULL);
          CREATE UNIQUE INDEX catalogue_position ON catalogue(position);
          CREATE TABLE aliases(id TEXT PRIMARY KEY,canonical TEXT NOT NULL REFERENCES catalogue(id));
          CREATE INDEX aliases_canonical ON aliases(canonical);
          CREATE TABLE lecture_summaries(id TEXT PRIMARY KEY,position INTEGER,content TEXT NOT NULL);
          CREATE TABLE problem_projections(id TEXT PRIMARY KEY,patch BLOB NOT NULL,knowledge BLOB NOT NULL,error TEXT);
          CREATE TABLE training_lists(id TEXT PRIMARY KEY,position INTEGER NOT NULL,content TEXT NOT NULL);
          CREATE TABLE derived_assets(sha256 TEXT PRIMARY KEY,mime TEXT NOT NULL,data BLOB NOT NULL);
        ''')
        db.executemany('INSERT INTO catalogue VALUES(?,?,?,?)', ((row['id'], index, zlib.compress(dump(row).encode('utf-8'), 6), dump(project_row(row))) for index, row in enumerate(rows)))
        db.executemany('INSERT INTO aliases VALUES(?,?)', sorted(aliases.items()))
        lectures = store.library.lecture_entries()
        db.executemany('INSERT INTO lecture_summaries VALUES(?,?,?)', [(identity,index,dump(lecture_library.summary(entry))) for index,(identity,entry) in enumerate(lectures.items())])
        store.training_data=lambda:{'rows':rows}
        public_lists=store.public_training_lists()
        db.executemany('INSERT INTO training_lists VALUES(?,?,?)',[(row['id'],index,dump(row)) for index,row in enumerate(public_lists)])
        allowed=set('id title markdown url samples limits judge statementAvailable statementError statementLoading statementVersion statementPdf currentSourceMarkdown statementSupplement images attachments problemType localJudgeSupported translation translationAvailable autoTranslate templatePractice nativeSamplePolicy'.split())
        assets=AssetLibrary(store,cache_dir=ROOT/'.backups/native-public-input')
        def existing_asset(sha,mime,data):
            # Reuse original bytes in the existing read-only public database.
            # Inline public resources not in its asset table are deduplicated
            # here as original bytes. No private cache or network is consulted.
            with store.library.connection() as source:
                if not source.execute('SELECT 1 FROM statement_assets WHERE sha256=?',(sha,)).fetchone():
                    db.execute('INSERT OR IGNORE INTO derived_assets VALUES(?,?,?)',(sha,mime,data))
        try:
            for index,row in enumerate(rows):
                identity=row['id']
                try:
                    with store.library.connection() as source:
                        original=source.execute('SELECT content FROM statements WHERE problem_id=?',(identity,)).fetchone()
                    original=json.loads(original[0]) if original else {}
                    public=assets.problem(identity,fetch=False)
                    bundle=assets.bundle(identity)
                    public['nativeSamplePolicy']={'schema':1,'supported':bundle['scope']!='unsupported',
                        'nonunique':bool(bundle.get('nonunique')),'caseInsensitive':bool(bundle.get('caseInsensitive')),
                        'checkerUnavailable':bool(bundle.get('checker')),'sourceScope':bundle['scope']}
                    header=dehydrate({k:v for k,v in public.items() if k in allowed},existing_asset)
                    selected=store.encode_row(store.row(identity))
                    enriched=enrich_row(selected,statement=public.get('markdown'),official_tags=public.get('officialTags'))
                    knowledge={k:enriched[k] for k in ['tags','knowledge','knowledgeAnalysis'] if k in enriched}
                    patch=list(patch_values({k:v for k,v in original.items() if k in allowed},header))
                    db.execute('INSERT INTO problem_projections VALUES(?,?,?,NULL)',(identity,zlib.compress(dump(patch).encode(),6),zlib.compress(dump(knowledge).encode(),6)))
                except (ValueError,RuntimeError,OSError) as error:
                    db.execute('INSERT INTO problem_projections VALUES(?,?,?,?)',(identity,zlib.compress(b'[]'),zlib.compress(b'{}'),str(error)[:300]))
                if index and index%3000==0:print(f'Compiled {index}/{len(rows)} problem projections',flush=True)
            events=public_replay_events(store,assets,rows)
        finally:assets.close()
        metadata = {'format': 4, 'source': before, 'revision': revision, 'statuses': list(status_report.STATES),
                    'categories': store.categories(), 'lectureRevision': store.library.metadata().get('revision', '0'),
                    'curationVersion': lecture_library.C.VERSION,'replayEvents':events}
        db.executemany('INSERT INTO metadata VALUES(?,?)', [(key, dump(value)) for key, value in metadata.items()])
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Native catalogue integrity failed')
    db.close()
    if signature(seed) != before:
        raise RuntimeError('Public seed changed during build; unfinished output preserved')
    # This is a generated public artifact, never an account database.
    os.replace(staging, destination)
    quizzes_tree = ast.parse((ROOT / 'backend/learning_summary.py').read_text(encoding='utf-8-sig'))
    quizzes = next(ast.literal_eval(node.value) for node in quizzes_tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'QUIZZES' for target in node.targets))
    (ROOT / 'backend/resources/native-quizzes.json').write_text(dump(quizzes) + '\n', encoding='utf-8')
    print(f'Native public view: {len(rows)} catalogue rows, {len(aliases)} aliases, {len(lectures)} lectures; {destination.stat().st_size} bytes')


if __name__ == '__main__':
    build()
