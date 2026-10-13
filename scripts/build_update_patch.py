"""Create a small release delta against a verified public package manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from update_patch import safe_name


def build(package, baseline, from_version, output):
    version = (package / 'VERSION').read_text().strip()
    def public(values):
        result = {}
        for name, sha in values.items():
            try: safe_name(name)
            except ValueError: continue
            result[name] = sha
        return result
    baseline_files=json.loads(baseline.read_text(encoding='utf-8'))
    package_files={p.relative_to(package).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in package.rglob('*') if p.is_file()}
    if {n:h for n,h in baseline_files.items() if n.startswith('compiler/')} != {n:h for n,h in package_files.items() if n.startswith('compiler/')}:
        raise ValueError('编译工具发生变化，需要单独发布工具链升级，不能隐藏在程序增量中')
    base = public(baseline_files)
    files = public(package_files)
    changed = sorted(name for name in files if files[name] != base.get(name))
    manifest = {'schema': 1, 'version': version, 'fromVersion': from_version, 'base': base, 'files': files, 'changed': changed}
    output.mkdir(parents=True, exist_ok=True)
    path = output / f'TB-Update-{from_version}-to-{version}-win64.zip'
    with zipfile.ZipFile(path, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr('update.json', json.dumps(manifest, ensure_ascii=False))
        for name in changed: archive.write(package / name, 'files/' + name)
    print(json.dumps({'path': str(path), 'bytes': path.stat().st_size, 'changedFiles': len(changed), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--package', required=True, type=Path)
    p.add_argument('--baseline', required=True, type=Path)
    p.add_argument('--from-version', required=True)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    build(args.package, args.baseline, args.from_version, args.output)
