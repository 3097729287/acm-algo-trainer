"""Restore release provenance shipped through legacy-compatible resource paths."""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
import re
import stat
import sys
import tempfile


LOG = logging.getLogger('tb.desktop.release_metadata')
LIMITS = {'BUILD-INFO.json': 256 * 1024, 'SOURCE-MANIFEST.json': 4 * 1024 * 1024}


def _regular_path(root: Path, path: Path, *, optional=False) -> bool:
    """Check fixed paths without following a symlink or Windows junction."""
    parts = [root, *[root.joinpath(*path.relative_to(root).parts[:i])
                    for i in range(1, len(path.relative_to(root).parts) + 1)]]
    for entry in parts:
        try:
            info = entry.lstat()
        except FileNotFoundError:
            if optional and entry == path:
                return False
            raise ValueError('missing release metadata') from None
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400):
            raise ValueError('linked release metadata path')
        expected = stat.S_ISREG if entry == path else stat.S_ISDIR
        if not expected(info.st_mode):
            raise ValueError('invalid release metadata path type')
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('release metadata outside installation')
    return True


def _read(root: Path, path: Path, limit: int, *, optional=False) -> bytes | None:
    if not _regular_path(root, path, optional=optional):
        return None
    with path.open('rb') as stream:
        value = stream.read(limit + 1)
    if len(value) > limit:
        raise ValueError('release metadata exceeds size limit')
    return value


def _stage(root: Path, value: bytes) -> Path:
    fd, name = tempfile.mkstemp(prefix='.tb-release-metadata-', dir=root)
    path = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


def refresh_release_metadata(app_dir: Path) -> dict:
    """Only frozen releases may replace the two fixed root metadata files.

    Older update helpers allow resources/ but reject new root filenames. The
    packaged copies are validated together before either root file is changed.
    This function never reads or writes personal state, caches, or databases.
    """
    if not getattr(sys, 'frozen', False):
        return {'status': 'source'}
    staged = {}
    replaced = []
    previous = {}
    root = Path(os.path.abspath(app_dir))
    try:
        version = _read(root, root / 'VERSION', 128).decode('utf-8').strip()
        if not re.fullmatch(r'\d+\.\d+\.\d+', version):
            raise ValueError('invalid installed version')
        values = {name: _read(root, root / 'resources' / name, limit)
                  for name, limit in LIMITS.items()}
        build = json.loads(values['BUILD-INFO.json'])
        manifest = json.loads(values['SOURCE-MANIFEST.json'])
        if not isinstance(build, dict) or not isinstance(manifest, dict):
            raise ValueError('invalid release metadata document')
        if build.get('version') != version:
            raise ValueError('release metadata version mismatch')
        if not isinstance(build.get('commit'), str) or not re.fullmatch(r'[a-fA-F0-9]{40}', build['commit']):
            raise ValueError('invalid release source commit')
        expected = hashlib.sha256(values['SOURCE-MANIFEST.json']).hexdigest()
        if build.get('sourceManifestSha256') != expected:
            raise ValueError('release source manifest checksum mismatch')
        if build.get('sourceManifest', 'SOURCE-MANIFEST.json') != 'SOURCE-MANIFEST.json':
            raise ValueError('invalid release source manifest name')
        # Validate both destinations before writing either. Optional root files
        # are absent in some legacy packages; existing personal paths are never
        # inferred from fields in these documents.
        previous = {name: _read(root, root / name, limit, optional=True)
                    for name, limit in LIMITS.items()}
        changed = [name for name in ('SOURCE-MANIFEST.json', 'BUILD-INFO.json')
                   if previous[name] != values[name]]
        if not changed:
            return {'status': 'current'}
        for name in changed:
            staged[name] = _stage(root, values[name])
        for name in changed:
            _regular_path(root, root / name, optional=True)
            os.replace(staged[name], root / name)
            replaced.append(name)
        LOG.info('Release provenance refreshed for version %s', version)
        return {'status': 'updated', 'files': changed}
    except Exception as issue:
        # Roll back completed replacements on a second-file write failure.
        # Errors here cannot stop the app from using its existing personal data.
        for name in reversed(replaced):
            try:
                _regular_path(root, root / name)
                if previous[name] is None:
                    (root / name).unlink()
                else:
                    rollback = _stage(root, previous[name])
                    staged['rollback-' + name] = rollback
                    os.replace(rollback, root / name)
            except Exception:
                LOG.exception('Could not restore previous release provenance')
        LOG.warning('Release provenance refresh skipped: %s', type(issue).__name__)
        return {'status': 'error', 'error': type(issue).__name__}
    finally:
        for path in staged.values():
            try:
                path.unlink(missing_ok=True)
            except OSError:
                LOG.warning('Could not remove release provenance staging file')
