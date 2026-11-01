"""Receive a public teaching checkout without replacing the current library.

The handoff checkout stays read only. Files are merged against the shared Git
ancestor; unrelated program/content fixes remain in this checkout. A private
SHA-256 receipt records every received file and each previous local file.
Library rows are subsequently merged by core7_import with program checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SAVE = ROOT / '.backups/next-150/core7-handoff'
PUBLIC_SUFFIXES = {'.cpp', '.md', '.py', '.json', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.mjs', '.jsx', '.html'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args, missing=False):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True)
    if missing and result.returncode:
        return None
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', errors='replace'))
    return result.stdout


def selected(source):
    files = set()
    for folder in ('data/core7-editorials', 'docs/foundations'):
        files.update(p for p in (source / folder).rglob('*') if p.is_file() and p.suffix in PUBLIC_SUFFIXES and '__pycache__' not in p.parts)
    files.update(p for p in (source / 'scripts').glob('core7*') if p.is_file() and p.suffix in PUBLIC_SUFFIXES)
    files.update(p for p in (source / 'docs').glob('core7*.md') if p.is_file())
    files.update(p for p in (source / 'frontend/tests').glob('core7*') if p.is_file() and p.suffix in PUBLIC_SUFFIXES)
    return sorted(files)


def run(source, apply=False):
    source = source.resolve(strict=True)
    if source == ROOT or source.is_relative_to(ROOT):
        raise ValueError('Use a separate handoff checkout')
    received = source / '.backups/core7-editorials-20261030'
    authored = json.loads((received / 'authored.json').read_text('utf-8'))
    proof = json.loads((received / 'verification.json').read_text('utf-8'))
    verified = {(p['pid'], p['method']): p for p in proof}
    for entry in authored:
        record = verified[entry['pid'], entry['method']]
        assert record['passed'] and record['programSha256'] == entry['programSha256']
        assert set(entry['variants']) == {'default', 'detailed'}
        program = source / 'data/core7-editorials' / entry['pid'] / entry['method'] / 'a.cpp'
        assert sha(program.read_text('utf-8').encode('utf-8')) == entry['programSha256'], str(program)
    base = git(ROOT, 'merge-base', 'HEAD', git(source, 'rev-parse', 'HEAD').decode().strip()).decode().strip()
    SAVE.mkdir(parents=True, exist_ok=True)
    dry_path = SAVE / 'dry-run.json'
    cached = json.loads(dry_path.read_text('utf-8')) if apply and dry_path.exists() else {}
    cached_files = {p['path']: p for p in cached.get('files', [])} if cached.get('commonAncestor') == base else {}
    pending = []
    receipt = []
    for path in selected(source):
        relative = path.relative_to(source)
        target = ROOT / relative
        incoming = path.read_bytes()
        current = target.read_bytes() if target.exists() else None
        cached_file = cached_files.get(relative.as_posix(), {})
        current_sha = sha(current) if current is not None else None
        cached_valid = cached_file.get('sourceSha256') == sha(incoming) and cached_file.get('previousSha256') == current_sha
        cached_content = incoming if cached_file.get('mergedSha256') == sha(incoming) else current if current is not None and cached_file.get('mergedSha256') == current_sha else None
        if cached_valid and cached_content is not None:
            receipt.append(cached_file)
            if current != cached_content:
                pending.append((relative, current, cached_content))
            continue
        original = git(ROOT, 'show', f'{base}:{relative.as_posix()}', missing=True)
        text_file = path.suffix not in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
        normal = lambda value: value.replace(b'\r\n', b'\n') if value is not None and text_file else value
        merged = incoming
        if current is not None and normal(current) == normal(incoming):
            merged = current
        elif current is not None and normal(current) != normal(original):
            if normal(incoming) == normal(original):
                merged = current
            elif original is None:
                raise ValueError('Different independently created file: ' + str(relative))
            else:
                scratch = SAVE / 'merge' / relative
                scratch.parent.mkdir(parents=True, exist_ok=True)
                versions = [scratch.with_name(scratch.name + suffix) for suffix in ('.ours', '.base', '.theirs')]
                for destination, content in zip(versions, (current, original, incoming)):
                    destination.write_bytes(normal(content))
                result = subprocess.run(['git', 'merge-file', '-p', *map(str, versions)], capture_output=True)
                if result.returncode:
                    raise ValueError('Handoff needs a manual merge: ' + str(relative))
                merged = result.stdout
        receipt.append({'path': relative.as_posix(), 'sourceSha256': sha(incoming),
                        'previousSha256': sha(current) if current is not None else None, 'mergedSha256': sha(merged)})
        if current != merged:
            pending.append((relative, current, merged))
    if apply:
        for relative, current, merged in pending:
            target = ROOT / relative
            assert (target.read_bytes() if target.exists() else None) == current, 'Concurrent edit: ' + str(relative)
            if current is not None:
                backup = SAVE / 'before' / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                if backup.exists():
                    assert backup.read_bytes() == current, 'Previous handoff backup differs: ' + str(relative)
                else:
                    backup.write_bytes(current)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(merged)
            assert sha(target.read_bytes()) == sha(merged)
        out = ROOT / '.backups/core7-editorials-20261030'
        for name in ('authored.json', 'verification.json', 'scope.json'):
            target = out / name
            target.parent.mkdir(parents=True, exist_ok=True)
            assert not target.exists(), 'Retain the existing verification run: ' + str(target)
            shutil.copy2(received / name, target)
        # Cached public statements and original verification logs are evidence,
        # not personal databases. Keep them outside distributed source tables.
        for folder in ('statements', 'verification'):
            for path in (received / folder).rglob('*'):
                if not path.is_file() or path.suffix not in {'.json', '.log'}:
                    continue
                target = out / path.relative_to(received)
                target.parent.mkdir(parents=True, exist_ok=True)
                assert not target.exists()
                shutil.copy2(path, target)
                assert sha(path.read_bytes()) == sha(target.read_bytes())
    result = {'source': str(source), 'sourceCommit': git(source, 'rev-parse', 'HEAD').decode().strip(),
              'commonAncestor': base, 'problems': len({x['problemId'] for x in authored}),
              'methods': len(authored), 'articles': 2 * len(authored), 'checkedProgramHashes': len(authored),
              'receivedFiles': len(receipt), 'changedFiles': len(pending), 'applied': apply,
              'sourceUnchanged': True, 'personalDatabasesOpened': False, 'installationChanged': False, 'files': receipt}
    (SAVE / ('receipt.json' if apply else 'dry-run.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    run(args.source, args.apply)
