"""Prepare a public, dependency-complete runtime; does not connect or deploy."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    version = json.loads((source / 'package.json').read_text(encoding='utf-8'))['version']
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    folder = output / ('runtime.next-' + version)
    if folder.exists():
        raise SystemExit('The stage already exists; choose a new output directory.')
    folder.mkdir()
    for name in ('src', 'mysql', 'scripts'):
        if (source / name).is_symlink() or any(path.is_symlink() for path in (source / name).rglob('*')):
            raise SystemExit('Runtime source directories must not contain symbolic links.')
        shutil.copytree(source / name, folder / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('package.json', 'package-lock.json', 'Caddyfile'):
        if (source / name).is_symlink():
            raise SystemExit('Runtime source files must not be symbolic links.')
        shutil.copy2(source / name, folder / name)
    if not (folder / 'mysql/006_public_progress.sql').is_file():
        raise SystemExit('Public progress migration 006 is required for this runtime.')
    npm = shutil.which('npm.cmd' if sys.platform == 'win32' else 'npm')
    if not npm:
        raise SystemExit('npm is required to prepare production dependencies.')
    subprocess.run([npm, 'ci', '--omit=dev', '--ignore-scripts', '--no-audit', '--no-fund'],
                   cwd=folder, check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if list(folder.rglob('*.node')):
        raise SystemExit('Native extensions cannot be copied across operating systems.')
    subprocess.run(['node', '--input-type=module', '-e', "await import('./src/server.mjs')"],
                   cwd=folder, check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    files = sorted(path for path in folder.rglob('*') if path.is_file())
    lines = []
    for path in files:
        relative = path.relative_to(folder).as_posix()
        if path.is_symlink() or any(part in {'.env', 'secrets', 'state', 'backups'} for part in path.relative_to(folder).parts) or path.suffix.lower() in {'.pem', '.key', '.sqlite', '.sqlite3', '.db'}:
            raise SystemExit('Unexpected private path or symbolic link in runtime.')
        lines.append(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + relative)
    (folder / 'runtime-manifest.sha256').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    artifact = output / ('TB-account-service-' + version + '.tar.gz')
    def public_permissions(info):
        # Windows source permissions must not leave the non-root container
        # unable to traverse/read its public runtime after extraction.
        info.mode = 0o755 if info.isdir() else 0o644
        info.uid = info.gid = 0
        info.uname = info.gname = 'root'
        return info
    with tarfile.open(artifact, 'w:gz', compresslevel=6) as archive:
        archive.add(folder, arcname=folder.name, filter=public_permissions)
    report = {'version': version, 'artifact': artifact.name, 'files': len(files) + 1,
              'bytes': artifact.stat().st_size, 'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()}
    (output / 'runtime-build-info.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
