"""Merge already-delivered contest content from its exact Git commits.

This imports public source only. It never opens an installed library, personal
database, original authoring archive or release feed. Library tables are merged
by stable identities, preserving unrelated editorial and statement revisions.
Conflicting concurrent edits stop before any source file is changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMMITS = ('ecdf5d31', '6b6fbbf2', '3e4550e8')
TABLE_KEYS = {
    'problems.json': ('id',),
    'solutions.json': ('problem_id',),
    'detailed_solutions.json': ('problem_id',),
    'statements.json': ('problem_id',),
    'solution_methods.json': ('problem_id',),
    'links.json': ('problem_id', 'lecture_id'),
}
MISSING = object()


def git(*args, missing=False):
    result = subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True)
    if result.returncode and missing:
        return None
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', errors='replace'))
    return result.stdout


def digest(value):
    return hashlib.sha256(value).hexdigest() if value is not None else None


def merge_value(base, current, incoming, location):
    if current == incoming or incoming == base:
        return current
    if current == base:
        return incoming
    if all(isinstance(value, dict) for value in (base, current, incoming)):
        merged = dict(current)
        for key in dict.fromkeys([*base, *incoming]):
            value = merge_value(base.get(key, MISSING), current.get(key, MISSING),
                                incoming.get(key, MISSING), f'{location}.{key}')
            if value is MISSING:
                merged.pop(key, None)
            else:
                merged[key] = value
        return merged
    raise ValueError('Concurrent content conflict: ' + location)


def merge_rows(base, current, incoming, name):
    keys = TABLE_KEYS[name]

    def index(rows):
        result = {}
        for row in rows:
            identity = tuple(row[key] for key in keys)
            if identity in result:
                raise ValueError(f'Duplicate {name} identity: {identity!r}')
            result[identity] = row
        return result

    old, ours, theirs = map(index, (base, current, incoming))
    changed = [identity for identity in dict.fromkeys([*old, *theirs])
               if old.get(identity, MISSING) != theirs.get(identity, MISSING)]
    merged = dict(ours)
    for identity in changed:
        before = old.get(identity, MISSING)
        after = theirs.get(identity, MISSING)
        if after is MISSING:
            raise ValueError(f'Delivered content would remove a record: {name} {identity!r}')
        merged[identity] = merge_value(before, ours.get(identity, MISSING), after,
                                      f'{name}[{identity!r}]')
    # Dict insertion order preserves the complete current table's identities.
    for identity, row in ours.items():
        if identity not in changed:
            assert merged[identity] == row
    return list(merged.values()), changed


def allowed(path):
    return (path.startswith('data/contest-editorials/')
            or path.startswith('data/library/') and Path(path).name in TABLE_KEYS
            or path in {'docs/three-contests-20261102.md', 'docs/div3-1131-20261102.md',
                        'docs/editorial-policy.md'}
            or path.startswith('frontend/tests/three-contests')
            or path.startswith('frontend/tests/cf2278')
            or path.startswith('scripts/three_contests_')
            or path.startswith('scripts/cf2278_')
            or path == 'scripts/verify_three_contests.py')


def run(evidence, apply=False):
    evidence = evidence.resolve()
    if not evidence.is_relative_to((ROOT / '.backups').resolve()):
        raise ValueError('Evidence must remain in this checkout .backups')
    evidence.mkdir(parents=True, exist_ok=True)
    prior=evidence/'receipt.json'
    if prior.is_file():
        receipt=json.loads(prior.read_text('utf-8'))
        final={record['path']:record['mergedSha256'] for record in receipt['files']}
        if tuple(receipt.get('commits',()))==COMMITS and all(
                (ROOT/path).is_file() and digest((ROOT/path).read_bytes())==value
                for path,value in final.items()):
            print(json.dumps({'commits':COMMITS,'applied':False,'alreadyImported':True,
                              'changedFiles':0,'installationChanged':False}))
            return
    originals, pending, records, tables = {}, {}, [], []
    for short in COMMITS:
        commit = git('rev-parse', short).decode().strip()
        paths = git('diff-tree', '--no-commit-id', '--name-only', '-r', '-z', commit).decode('utf-8').split('\0')
        for path in filter(None, paths):
            if not allowed(path) or Path(path).is_absolute() or '..' in Path(path).parts:
                raise ValueError('Unexpected delivered file: ' + path)
            target = ROOT / path
            if path not in originals:
                originals[path] = target.read_bytes() if target.exists() else None
            current = pending.get(path, originals[path])
            base = git('show', f'{commit}^:{path}', missing=True)
            incoming = git('show', f'{commit}:{path}', missing=True)
            if incoming is None:
                raise ValueError('Delivered content removes a file: ' + path)
            if path.startswith('data/library/'):
                merged, changed = merge_rows(json.loads(base or b'[]'), json.loads(current or b'[]'),
                                             json.loads(incoming), Path(path).name)
                content = (json.dumps(merged, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
                tables.append({'commit': commit, 'path': path, 'changedIdentities': changed,
                               'previousRows': len(json.loads(current or b'[]')), 'mergedRows': len(merged)})
            else:
                binary = Path(path).suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
                normal = lambda value: value if binary or value is None else value.replace(b'\r\n', b'\n')
                if normal(current) == normal(incoming) or normal(incoming) == normal(base):
                    content = current
                elif current is None or normal(current) == normal(base):
                    content = incoming
                elif base is not None and not binary:
                    scratch = evidence / 'merge' / short / path
                    scratch.parent.mkdir(parents=True, exist_ok=True)
                    versions = [scratch.with_name(scratch.name + suffix) for suffix in ('.ours', '.base', '.theirs')]
                    for filename, value in zip(versions, (current, base, incoming)):
                        filename.write_bytes(normal(value))
                    result = subprocess.run(['git', 'merge-file', '-p', *map(str, versions)], capture_output=True)
                    if result.returncode:
                        raise ValueError('Concurrent source conflict: ' + path)
                    content = result.stdout
                else:
                    raise ValueError('Different independently-created delivered file: ' + path)
            assert content is not None
            pending[path] = content
            records.append({'commit': commit, 'path': path, 'sourceSha256': digest(incoming),
                            'previousSha256': digest(current), 'mergedSha256': digest(content)})
    changes = {path: value for path, value in pending.items() if value != originals[path]}
    # Check every precondition before creating the first source-file mutation.
    for path in changes:
        target = ROOT / path
        assert (target.read_bytes() if target.exists() else None) == originals[path], 'Concurrent edit: ' + path
    if apply:
        for path, content in changes.items():
            target = ROOT / path
            before = originals[path]
            if before is not None:
                backup = evidence / 'before' / path
                backup.parent.mkdir(parents=True, exist_ok=True)
                if backup.exists():
                    assert backup.read_bytes() == before, 'Retain different original backup: ' + path
                else:
                    backup.write_bytes(before)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            assert digest(target.read_bytes()) == digest(content)
    report = {'commits': COMMITS, 'applied': apply, 'changedFiles': len(changes),
              'tables': tables, 'files': records, 'personalDatabasesOpened': False,
              'installationChanged': False, 'originalArchiveChanged': False}
    (evidence / ('receipt.json' if apply else 'dry-run.json')).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key not in {'tables', 'files'}}, ensure_ascii=False))
    for record in tables:
        print(json.dumps({key: value for key, value in record.items() if key != 'changedIdentities'}
                         | {'changedIdentities': len(record['changedIdentities'])}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=ROOT / '.backups/next-150/delivered-contests')
    parser.add_argument('--apply', action='store_true')
    arguments = parser.parse_args()
    run(arguments.evidence, arguments.apply)
