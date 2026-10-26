"""Retire known official user binaries after preserving all private directories."""
from __future__ import annotations

import base64
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import subprocess
import threading
import time

PRIVATE = {'state', 'cache', 'backups', 'logs', 'admin-workspace'}
REPOSITORY = '3097729287/acm-algo-trainer'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def linked(path):
    return path.is_symlink() or getattr(path, 'is_junction', lambda: False)()


def safe_file(root, name):
    parts = PurePosixPath(name).parts
    if not parts or parts[0] in PRIVATE or '..' in parts or '\\' in name or ':' in name or name.startswith('/'):
        raise ValueError('Unsafe legacy program path')
    target = root.joinpath(*parts)
    if not target.resolve().is_relative_to(root.resolve()) or any(linked(root.joinpath(*parts[:i])) for i in range(len(parts)+1)):
        raise ValueError('Legacy path leaves its program directory')
    return target


def identify(root, app, catalog):
    root = Path(root).absolute()
    if any(linked(path) for path in (root, *root.parents)): return None
    root, app = root.resolve(), Path(app).resolve()
    if (root == app or app.is_relative_to(root) or root.is_relative_to(app) or linked(Path(root)) or
            (root/'.git').exists() or (root/'backend').is_dir() or (root/'admin-workspace').exists() or
            (root/'TB管理员版.exe').exists() or (root/'ToBe管理员版.exe').exists()): return None
    known = {}
    for version, executables in catalog['versions'].items():
        for name, digest in executables.items():
            executable = safe_file(root, name)
            if name not in known: known[name] = sha(executable) if executable.is_file() else None
            if known[name] == digest:
                # A version file can be modified; an official executable hash
                # provides the product identity, independently of its folder.
                return {'root': root, 'version': version, 'executable': executable}
    return None


def copy_private(source, target):
    """Copy every private file; SQLite online backup includes committed WAL."""
    for directory, children, names in os.walk(source, followlinks=False):
        folder = Path(directory)
        if linked(folder) or any(linked(folder/name) for name in children):
            raise ValueError('Linked personal directory; original program retained')
        relative = folder.relative_to(source)
        (target/relative).mkdir(parents=True, exist_ok=True)
        for name in names:
            path, destination = folder/name, target/relative/name
            if linked(path): raise ValueError('Linked personal file; original program retained')
            if name.endswith(('-wal', '-shm', '-journal')):
                base = folder/name.rsplit('-', 1)[0]
                if base.is_file():
                    with base.open('rb') as stream:
                        if stream.read(16) == b'SQLite format 3\x00': continue
            with path.open('rb') as stream: sqlite = stream.read(16) == b'SQLite format 3\x00'
            if sqlite:
                deadline = time.monotonic() + 20
                def progress(status, remaining, total):
                    if time.monotonic() > deadline: raise TimeoutError('Personal database remained busy')
                with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True, timeout=1)) as source_db, closing(sqlite3.connect(destination)) as backup_db:
                    source_db.backup(backup_db, pages=128, progress=progress, sleep=.05)
                    if backup_db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok': raise ValueError('Personal backup failed integrity check')
            else:
                shutil.copy2(path, destination)
                if sha(path) != sha(destination): raise ValueError('Personal backup changed during copying')


def preserve(candidate, app):
    source = candidate['root']
    key = hashlib.sha256(str(source).casefold().encode()).hexdigest()[:20]
    backup = app/'state/backups/legacy-programs'/key
    complete = backup/'complete.json'
    if complete.is_file():
        # Never mistake an old backup for protection of newly changed data.
        backup = backup.with_name(key+'-'+str(time.time_ns()))
        complete = backup/'complete.json'
    backup.mkdir(parents=True, exist_ok=False)
    for name in sorted(PRIVATE):
        directory = source/name
        if directory.exists(): copy_private(directory, backup/name)
    complete.write_text(json.dumps({'source': str(source), 'version': candidate['version'], 'complete': True}), encoding='utf8')
    return backup


def retire(candidate, app, catalog, *, running=()):
    source = candidate['root'].resolve()
    if any(Path(path).resolve().is_relative_to(source) for path in running):
        return {'status': 'running', 'removed': 0}
    fresh = identify(source, app, catalog)
    if not fresh: return {'status': 'unrecognized', 'removed': 0}
    backup = preserve(fresh, app)
    # Removing the verified entry point first also prevents a new old-version
    # process from opening its frontend halfway through retirement.
    executable = fresh['executable']
    if sha(executable) not in catalog['versions'][fresh['version']].values():
        return {'status': 'changed', 'removed': 0}
    executable.unlink()
    removed, retained = 1, 0
    # Only byte-for-byte known distributed files can be deleted. User-created
    # code, modified files, databases and unknown contents stay where they are.
    for name, digests in catalog['files'].items():
        target = safe_file(source, name)
        if target.is_file() and sha(target) in digests:
            try: target.unlink(); removed += 1
            except OSError: retained += 1
    directories = {source.joinpath(*PurePosixPath(name).parts[:i]) for name in catalog['files'] for i in range(1, len(PurePosixPath(name).parts))}
    for directory in sorted(directories, key=lambda p: len(p.parts), reverse=True):
        if directory.resolve().is_relative_to(source) and not linked(directory):
            try: directory.rmdir()
            except OSError: pass
    return {'status': 'retired', 'removed': removed, 'retained': retained, 'backup': str(backup)}


def powershell(script):
    encoded = base64.b64encode(('[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);'+script).encode('utf-16le')).decode()
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
                            capture_output=True, timeout=30, check=True,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    return json.loads(result.stdout.decode('utf-8-sig') or '{}')


def discover(app):
    """Registry, shortcuts, Downloads and conventional TB program locations."""
    if os.name != 'nt': return [], [], {}
    import winreg
    roots = {Path(os.environ.get('LOCALAPPDATA', ''))/'Programs/TB'}
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                key = winreg.OpenKey(hive, r'Software\Microsoft\Windows\CurrentVersion\Uninstall\{0F82D178-AC2B-4696-96C1-1A210F72B509}_is1', 0, winreg.KEY_READ|view)
                with key: roots.add(Path(winreg.QueryValueEx(key, 'InstallLocation')[0]))
            except OSError: pass
    shortcut_roots = [Path.home()/'Desktop', Path(os.environ.get('APPDATA', ''))/'Microsoft/Windows/Start Menu/Programs']
    for parent in app.parents:
        if parent.name.casefold() == 'tb': shortcut_roots.append(parent); break
    literal = lambda value: "'"+str(value).replace("'", "''")+"'"
    script = "$ErrorActionPreference='Stop';$w=New-Object -ComObject WScript.Shell;$links=@{};"
    script += 'foreach($r in @('+','.join(map(literal, shortcut_roots))+')){if(Test-Path -LiteralPath $r){Get-ChildItem -LiteralPath $r -Filter *.lnk -File -Depth 3 -ErrorAction SilentlyContinue|ForEach-Object{$t=$w.CreateShortcut($_.FullName).TargetPath;if($t -match "[\\\\/]TB(?:新版)?\\.exe$"){$links[$_.FullName]=$t}}}};'
    script += '$running=@(Get-CimInstance Win32_Process|Where-Object{$_.Name -match "^TB.*\\.exe$"}|ForEach-Object{$_.ExecutablePath});@{shortcuts=$links;running=$running}|ConvertTo-Json -Compress -Depth 4'
    windows = powershell(script)
    links = windows.get('shortcuts', {})
    roots.update(Path(target).parent for target in links.values())
    downloads = Path.home()/'Downloads'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
            downloads = Path(os.path.expandvars(winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]))
    except OSError: pass
    search = [downloads, Path.home()/'Desktop', app.parent]
    for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
        drive = Path(letter+':/')
        if drive.is_dir(): search.extend([drive, drive/'Downloads', drive/'Program Files', drive/'Program Files (x86)'])
    for directory in search:
        try: roots.update(path for path in directory.iterdir() if path.is_dir() and path.name.casefold().startswith(('tb', 'acm-algo-trainer')) and not linked(path))
        except OSError: pass
    candidates, visited = set(), 0
    for root in list(roots):
        if not root.is_dir(): continue
        for directory, children, names in os.walk(root, followlinks=False):
            folder = Path(directory); visited += 1
            children[:] = [name for name in children if name not in PRIVATE|{'compiler','_internal','frontend','resources','node_modules','.git','build','.backups'} and not linked(folder/name)]
            if len(folder.relative_to(root).parts) >= 3 or visited >= 3000: children.clear()
            if 'TB新版.exe' in names or 'TB.exe' in names: candidates.add(folder)
    return sorted(candidates), [path for path in windows.get('running', []) if path], links


def load_catalog():
    from paths import resource
    result = json.loads(resource('legacy-programs-v1.json').read_text(encoding='utf8'))
    if result.get('schema') != 1 or result.get('repository') != REPOSITORY: raise ValueError('Invalid legacy catalog')
    return result


def prepare(app):
    """For a fresh target, migrate the most recent known local workspace first."""
    app = Path(app).resolve()
    if (app/'state/tb-personal.sqlite3').exists(): return
    catalog = load_catalog()
    roots, running, _ = discover(app)
    choices = [item for root in roots if (item := identify(root, app, catalog))]
    choices = [item for item in choices if (item['root']/'state/tb-personal.sqlite3').is_file() and not any(Path(path).resolve().is_relative_to(item['root']) for path in running)]
    if not choices: return
    candidate = max(choices, key=lambda item: (item['root']/'state/tb-personal.sqlite3').stat().st_mtime_ns)
    recovery = preserve(candidate, app)
    # Copy into a fresh workspace only. Other old workspaces remain separate
    # recoveries; no private account tables are overwritten or mixed together.
    for name in ('state', 'cache'):
        if (recovery/name).exists(): shutil.copytree(recovery/name, app/name, dirs_exist_ok=True)


def redirect_shortcuts(links, old, app):
    selected = [path for path, target in links.items() if Path(target).parent.resolve() == old.resolve()]
    if not selected:
        return
    def literal(value):
        return "'" + str(value).replace("'", "''") + "'"
    script = '$w=New-Object -ComObject WScript.Shell;'
    for path in selected:
        script += f'$s=$w.CreateShortcut({literal(path)});$s.TargetPath={literal(app/"ToBe.exe")};$s.WorkingDirectory={literal(app)};$s.IconLocation={literal(app/"tb.ico")};$s.Save();'
    powershell(script + '@{}|ConvertTo-Json')


def start(app, ready):
    app = Path(app).resolve()
    def work():
        import logging
        catalog, completed = load_catalog(), set()
        while True:
            time.sleep(5 if not ready() else 1)
            if not ready(): continue
            try:
                roots, running, links = discover(app)
                for root in roots:
                    if str(root) in completed: continue
                    candidate = identify(root, app, catalog)
                    if not candidate: continue
                    result = retire(candidate, app, catalog, running=running)
                    if result['status'] != 'retired': continue
                    completed.add(str(root))
                    redirect_shortcuts(links, root, app)
                    report = app/'state/legacy-cleanup.json'
                    report.write_text(json.dumps({'last': str(root), **result}, ensure_ascii=False), encoding='utf8')
            except Exception as issue:
                logging.getLogger('tb.legacy').warning('Legacy cleanup deferred: %s', type(issue).__name__)
            time.sleep(60)
    threading.Thread(target=work, name='tb-legacy-cleanup', daemon=True).start()


def finish_install(app):
    """Run without opening a window or waiting for cloud-account sign-in."""
    app = Path(app).resolve()
    # A failed migration must stop retirement before any program is removed.
    prepare(app)
    catalog = load_catalog()
    roots, running, links = discover(app)
    results = []
    for root in roots:
        candidate = identify(root, app, catalog)
        if not candidate:
            continue
        try:
            result = retire(candidate, app, catalog, running=running)
            if result['status'] == 'retired':
                redirect_shortcuts(links, root, app)
            results.append({'source': str(root), **result})
        except (OSError, ValueError, TimeoutError, subprocess.SubprocessError) as error:
            # Preserve other workspaces even when one is busy or modified.
            results.append({'source': str(root), 'status': 'deferred', 'error': type(error).__name__})
    report = app/'state/legacy-install-cleanup.json'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({'results': results}, ensure_ascii=False), encoding='utf8')
    return results
