"""Verified, bounded automatic SQLite recovery points. Manual copies are private.

Only files created with this module's matching manifest can be retired. Legacy
copies, unknown files, symbolic links and manual recovery points are untouched.
"""
from contextlib import closing
import datetime as dt
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import sqlite3
import threading
import uuid

LOCK = threading.RLock()
POLICY = {'recent': 3, 'daily': 7, 'weekly': 4, 'maxCount': 14,
          'familyBytes': 256 * 1024 * 1024, 'rootBytes': 1024 * 1024 * 1024}
UTC = dt.timezone.utc


def _checksum(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''): digest.update(block)
    return digest.hexdigest()


def _inside(path, root):
    return not path.is_symlink() and path.resolve().is_relative_to(root.resolve())


def _ordinary_directory(path):
    try:
        return not path.is_symlink() and not (getattr(path.stat(), 'st_file_attributes', 0) & 0x400)
    except OSError:
        return False


def _records(root):
    result = []
    root = Path(root).resolve()
    if not root.is_dir(): return result
    for directory, children, names in os.walk(root, followlinks=False):
        folder = Path(directory)
        children[:] = [name for name in children if _ordinary_directory(folder / name)]
        for name in names:
            if not name.endswith('.recovery.json'): continue
            manifest = folder / name
            if not _inside(manifest, root): continue
            try:
                value = json.loads(manifest.read_text('utf8'))
                target = folder / value['file']
                if (value.get('schema') != 1 or value.get('automatic') is not True
                    or Path(value['file']).name != value['file']
                    or not re.fullmatch(r'[a-f0-9]{64}', value['sourceKey'])
                    or not re.fullmatch(r'[a-f0-9]{64}', value['sha256'])
                    or target.name + '.recovery.json' != name
                    or not target.is_file() or not _inside(target, root)): continue
                created = dt.datetime.fromisoformat(value['createdAt'])
                if created.tzinfo is None or target.stat().st_size != value['bytes']: continue
                result.append({**value, 'path': target, 'manifest': manifest, 'created': created})
            except (ValueError, OSError, TypeError, KeyError): continue
    return result


def verify(path, expected_sha256=None):
    """Open the recovery copy itself, rather than trusting a successful write."""
    path = Path(path)
    try:
        if expected_sha256 and _checksum(path) != expected_sha256: return False
        with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
            return db.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
    except (OSError, sqlite3.Error): return False


def preview(root, *, policy=None, now=None):
    """Return a reviewable automatic-retention plan without changing any file."""
    rules = {**POLICY, **(policy or {})}
    now = now or dt.datetime.now(UTC)
    records = _records(root)
    families = {}
    for record in records: families.setdefault(record['sourceKey'], []).append(record)
    protected, selected = set(), set()
    for values in families.values():
        values.sort(key=lambda item: (item['created'], item['file']), reverse=True)
        # No cleanup until two independently readable recovery points exist.
        valid = [item for item in values[:3] if verify(item['path'], item['sha256'])]
        if len(valid) < 2:
            protected.update(item['path'] for item in values)
            selected.update(item['path'] for item in values)
            continue
        protected.update(item['path'] for item in valid[:2])
        keep = {item['path'] for item in values[:rules['recent']]}
        days, weeks = set(), set()
        for item in values:
            age = (now.date() - item['created'].date()).days
            day = item['created'].date()
            week = item['created'].isocalendar()[:2]
            if 0 <= age < rules['daily'] and day not in days:
                keep.add(item['path']); days.add(day)
            if 0 <= age < 7 * rules['weekly'] and week not in weeks:
                keep.add(item['path']); weeks.add(week)
        ordered = [item for item in values if item['path'] in keep]
        selected.update(item['path'] for item in ordered[:rules['maxCount']])
        family_size = sum(item['bytes'] for item in values if item['path'] in selected)
        for item in reversed(values):
            if family_size <= rules['familyBytes']: break
            if item['path'] in selected and item['path'] not in protected:
                selected.remove(item['path']); family_size -= item['bytes']
    selected.update(protected)
    retained_bytes = sum(item['bytes'] for item in records if item['path'] in selected)
    for item in sorted(records, key=lambda item: (item['created'], item['file'])):
        if retained_bytes <= rules['rootBytes']: break
        if item['path'] in selected and item['path'] not in protected:
            selected.remove(item['path']); retained_bytes -= item['bytes']
    retired = [item for item in records if item['path'] not in selected]
    return {'files': records, 'retire': retired, 'count': len(records),
            'retainedCount': len(records)-len(retired), 'bytes': sum(item['bytes'] for item in records),
            'retainedBytes': retained_bytes, 'overBudget': retained_bytes > rules['rootBytes'], 'policy': rules}


def prune(root, *, policy=None, now=None):
    with LOCK:
        root = Path(root).resolve()
        plan = preview(root, policy=policy, now=now)
        for item in plan['retire']:
            target, manifest = item['path'], item['manifest']
            # Check final absolute paths immediately before each single-file delete.
            if not _inside(target, root) or not _inside(manifest, root): continue
            try:
                if target.stat().st_size != item['bytes']: continue
                target.unlink()
                manifest.unlink()
            except OSError:
                # A locked old recovery copy must not prevent saving new code.
                logging.getLogger('tb.backups').warning('Automatic recovery cleanup deferred')
        return plan


def snapshot(connection, source_path, directory, *, label='automatic', manual=False,
             budget_root=None, policy=None, now=None, suffix='.bak'):
    """Online WAL-aware copy, integrity/hash verification, then bounded retention."""
    now = now or dt.datetime.now(UTC)
    directory = Path(directory).resolve()
    if manual: directory /= 'manual'
    directory.mkdir(parents=True, exist_ok=True)
    source_path = Path(source_path).resolve()
    source_key = hashlib.sha256(str(source_path).casefold().encode('utf8')).hexdigest()
    if suffix not in ('.bak', '.sqlite3'): raise ValueError('Unsupported recovery suffix')
    safe_label = re.sub(r'[^A-Za-z0-9_-]+', '-', str(label)).strip('-')[:36] or 'automatic'
    name = source_path.name + ('.manual-' if manual else '.auto-') + safe_label + '-' + now.strftime('%Y%m%d-%H%M%S-%f') + '.' + uuid.uuid4().hex[:8] + suffix
    target = directory / name
    temporary = directory / (name + '.partial')
    with LOCK:
        try:
            with closing(sqlite3.connect(temporary)) as destination:
                connection.backup(destination)
                if destination.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise ValueError('SQLite recovery point failed integrity verification')
                # Compare the restored schema and the critical private record counts.
                tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                for table in ('training', 'drafts', 'submissions', 'contests', 'account_preferences'):
                    if table in tables and connection.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0] != destination.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]:
                        raise ValueError('SQLite recovery point record counts differ')
            checksum = _checksum(temporary)
            if not verify(temporary, checksum): raise ValueError('SQLite recovery point cannot be reopened')
            temporary.replace(target)
            value = {'schema': 1, 'automatic': not manual, 'sourceKey': source_key, 'file': name,
                     'createdAt': now.isoformat(), 'bytes': target.stat().st_size, 'sha256': checksum, 'label': label}
            (directory / (name + '.recovery.json')).write_text(json.dumps(value, sort_keys=True), 'utf8')
            if not manual: prune(budget_root or directory, policy=policy, now=now)
            return target
        finally:
            if temporary.is_file() and _inside(temporary, directory): temporary.unlink()
