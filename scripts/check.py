"""Offline checks, including the exact public SQLite file that will be distributed."""
import argparse
import json
import hashlib
from contextlib import ExitStack
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def library_check(path=None):
    source = ROOT / 'data' / 'library'
    explicit=path is not None
    path = Path(path).resolve() if explicit else ROOT / 'data' / 'library.sqlite3'
    if not explicit and not path.is_file() and source.is_dir():
        sys.path.insert(0, str(ROOT / 'backend'))
        sys.path.insert(0, str(ROOT / 'backend' / 'common'))
        from library import LibraryDatabase
        LibraryDatabase.from_source(source, path)
    if not path.is_file():
        raise AssertionError('Missing bundled library and its text source under data/library/')
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        counts = {table: db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                  for table in ('problems', 'solutions', 'detailed_solutions', 'statements', 'lectures', 'problem_lectures')}
        assert counts['problems'] >= counts['solutions'] >= 607
        assert not db.execute('SELECT problem_id FROM solutions WHERE NOT EXISTS (SELECT 1 FROM problems WHERE problems.id=solutions.problem_id)').fetchall()
        for row, in db.execute('SELECT raw FROM problems'):
            data = json.loads(row)
            assert (data['状态'], data['日期']) == ('未做', '')
        for path, in db.execute('SELECT source_path FROM solutions UNION ALL SELECT source_path FROM detailed_solutions'):
            assert not Path(path).is_absolute(), 'Absolute source path in public content'
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'statement_assets' in tables:
            known=set()
            for sha,mime,data in db.execute('SELECT sha256,mime,data FROM statement_assets'):
                assert hashlib.sha256(data).hexdigest()==sha,'Corrupt original statement asset'
                known.add(sha)
            sys.path.insert(0,str(ROOT/'backend'))
            if 'remote_statement_assets' in tables:
                from public_assets import validate_reference
                for sha,mime,size,url in db.execute('SELECT * FROM remote_statement_assets'):
                    validate_reference(sha,mime,size,url);known.add(sha)
            from statement_asset_store import references
            for content, in db.execute('SELECT content FROM statements'):
                assert references(json.loads(content))<=known,'Missing offline statement resources'
            for table in ('solutions','detailed_solutions'):
                for images, in db.execute('SELECT images FROM '+table):
                    assert references({'images':json.loads(images)})<=known,'Missing editorial resources: '+table
        assert not tables.intersection({'training', 'drafts', 'submissions', 'ranking_profile', 'documents'})
        if source.is_dir():
            manifest=source/'statement_assets.json'
            if manifest.exists():
                with ExitStack() as files:
                    streams={}
                    for item in json.loads(manifest.read_text('utf8')):
                        file=item['file'];assert file.startswith('statement-assets/') and '..' not in file
                        if file not in streams:streams[file]=files.enter_context((source/file).open('rb'))
                        streams[file].seek(item.get('offset',0));data=streams[file].read(item['bytes'])
                        assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256'],'Original source asset mismatch'
            expected = {row['id'] for row in json.loads((source/'problems.json').read_text('utf8'))}
            actual = {row[0] for row in db.execute('SELECT id FROM problems')}
            assert actual == expected, 'Bundled SQLite is stale; rebuild it with scripts/library_seed.py build'
    print('Bundled library: ' + json.dumps(counts), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--library-only', action='store_true')
    parser.add_argument('--library', type=Path, help='Exact isolated public seed selected for packaging')
    args = parser.parse_args()
    library_check(args.library)
    if args.library_only:
        return
    env = dict(os.environ, TB_OFFLINE='1')
    env['TB_CHECK_LIBRARY'] = str((args.library or ROOT / 'data/library.sqlite3').resolve())
    env['PYTHONPATH'] = os.pathsep.join(str(ROOT / p) for p in ('backend', 'backend/common', 'desktop'))
    # Tests and Store must read the same explicit public seed that was checked
    # above. Set the shared path before discovery imports modules by value;
    # no extra seed is copied into the source worktree.
    bootstrap = (
        'import os,runpy,sys; from pathlib import Path; import paths; '
        'paths.LIBRARY_SEED=Path(os.environ["TB_CHECK_LIBRARY"]); '
        'sys.argv=["unittest","discover","-s","backend","-p","test_*.py"]; '
        'runpy.run_module("unittest",run_name="__main__")'
    )
    subprocess.run([sys.executable, '-c', bootstrap],
                   cwd=ROOT, env=env, check=True)


if __name__ == '__main__':
    main()
