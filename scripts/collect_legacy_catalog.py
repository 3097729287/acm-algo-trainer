"""Maintainer-only: collect hashes of official user programs, never private data."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.request import getproxies

REPO = '3097729287/acm-algo-trainer'


def gh(*args):
    environment = dict(os.environ)
    proxies = getproxies()
    for scheme in ('http', 'https'):
        if proxies.get(scheme): environment[scheme.upper()+'_PROXY'] = proxies[scheme]
    for attempt in range(3):
        try:
            return subprocess.check_output(['gh', *args], env=environment, stderr=subprocess.PIPE, timeout=50,
                                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            if attempt == 2: raise RuntimeError('Official release metadata download failed; no catalog was published') from None


def allowed(name):
    path = PurePosixPath(name)
    return (not path.is_absolute() and '..' not in path.parts and '\\' not in name and ':' not in name and
            not re.search('admin|管理员', name, re.I) and
            (path.parts[0] in {'_internal', 'frontend', 'resources', 'compiler', 'licenses', 'data'} or len(path.parts) == 1) and
            path.parts[0] not in {'state', 'cache', 'backups', 'logs'})


def collect(output, cache):
    cache.mkdir(parents=True, exist_ok=True)
    releases = json.loads(gh('api', f'repos/{REPO}/releases?per_page=100'))
    selected = []
    for release in releases:
        version = release.get('tag_name', '').removeprefix('v')
        if not re.fullmatch(r'\d+\.\d+\.\d+', version) or tuple(map(int, version.split('.'))) >= (1, 3, 5): continue
        asset = next((a for a in release.get('assets', []) if a['name'] == 'RELEASE-MANIFEST.json'), None)
        if asset and asset['size'] <= 4*1024*1024:
            selected.append((version, asset))
    def fetch(entry):
        version, asset = entry
        target = cache/f'{version}.json'
        if not target.exists():
            data = gh('api', f'repos/{REPO}/releases/assets/{asset["id"]}', '-H', 'Accept: application/octet-stream')
            if asset.get('digest') and 'sha256:'+hashlib.sha256(data).hexdigest() != asset['digest']:
                raise ValueError('Official manifest checksum differs')
            target.write_bytes(data)
        return version, json.loads(target.read_text(encoding='utf-8-sig'))
    files, versions = {}, {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for version, manifest in pool.map(fetch, selected):
            executables = {name: sha for name, sha in manifest.items() if '/' not in name and name in {'TB新版.exe', 'TB.exe'} and re.fullmatch('[a-f0-9]{64}', sha)}
            if not executables: continue
            versions[version] = executables
            for name, sha in manifest.items():
                if allowed(name) and re.fullmatch('[a-f0-9]{64}', sha):
                    files.setdefault(name, set()).add(sha)
    if not versions: raise RuntimeError('No official legacy programs were verified')
    result = {'schema': 1, 'repository': REPO, 'beforeVersion': '1.3.5', 'versions': versions,
              'files': {name: sorted(values) for name, values in sorted(files.items())}}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':'))+'\n', encoding='utf8')
    print(json.dumps({'versions': sorted(versions), 'knownPaths': len(files), 'bytes': output.stat().st_size}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    args = parser.parse_args(); collect(args.output, args.cache)
