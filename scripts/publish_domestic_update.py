"""Publish verified user updates to the owned HTTPS service, manifest last."""
import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import sys

from release_assets import public_release_files

ROOT = Path(__file__).resolve().parents[1]
HOST = 'root@47.82.84.74'
REMOTE = '/opt/tb-leaderboard/updates'
CONTAINER = 'tb-leaderboard-caddy-1'
BASE = 'https://47.82.84.74/updates'


def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def publish(args):
    ssh = ['ssh', '-i', str(args.key.resolve()), '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', HOST, 'sh -s']
    def remote(script):
        result = subprocess.run(ssh, input=('set -eu\n'+script+'\n').encode(), capture_output=True, check=True)
        return result.stdout.decode('utf8')
    def upload(local, target):
        subprocess.run(['scp', '-i', str(args.key.resolve()), '-o', 'BatchMode=yes', str(local), HOST+':'+target], check=True)
    public = public_release_files(args.directory)
    info = json.loads((args.directory/'BUILD-INFO.json').read_text(encoding='utf8'))
    version, commit = info.get('version'), info.get('commit')
    if (not re.fullmatch(r'\d+\.\d+\.\d+', version or '') or not re.fullmatch('[a-f0-9]{40}', commit or '') or
            not info.get('sourcePushed') or info.get('workingTreeDirty') is not False):
        raise ValueError('Only a release from fixed, pushed source can be published')
    assets = [path for path in public if re.fullmatch(r'(?:ToBe|TB)-(?:Setup-'+re.escape(version)+r'-win64\.exe|Update-[\d.]+-to-'+re.escape(version)+r'-win64\.zip)', path.name)]
    if not any(path.suffix == '.exe' for path in assets): raise ValueError('The complete user installer is required')
    checksums = {}
    for line in (args.directory/'SHA256SUMS.txt').read_text(encoding='utf8').splitlines():
        digest, name = line.split(maxsplit=1); checksums[name.lstrip('*')] = digest
    for path in assets:
        if sha(path) != checksums.get(path.name): raise ValueError('Public checksum differs: '+path.name)
    args.work.mkdir(parents=True, exist_ok=True)
    previous = remote(f'if test -f {REMOTE}/stable/manifest-v1.json; then cat {REMOTE}/stable/manifest-v1.json; else echo "{{}}"; fi')
    history = json.loads(previous).get('releases', [])
    record = {'version': version, 'sourceCommit': commit,
              'notes': args.notes.read_text(encoding='utf8'),
              'assets': [{'name': path.name, 'size': path.stat().st_size, 'sha256': sha(path),
                          'url': f'{BASE}/assets/{version}/{path.name}'} for path in assets]}
    manifest = {'schema': 1, 'channel': 'stable', 'publishedAt': datetime.now(timezone.utc).isoformat(),
                'releases': [record]+[row for row in history if row['version'] != version][:99]}
    metadata = args.work/'manifest-v1.json'
    metadata.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    setup = next(asset for asset in record['assets'] if asset['name'].endswith('.exe'))
    page = args.work/f'release-{version}.html'
    page.write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ToBe '+version+'</title><style>body{font:17px/1.8 system-ui;background:#101116;color:#eee;max-width:850px;margin:7vh auto;padding:24px}a{color:#a99bff}pre{white-space:pre-wrap;font:inherit}code{word-break:break-all}</style><h1>ToBe '+version+'</h1><p><a href="'+setup['url']+'">下载 Windows 安装版</a></p><p>安装后自动检查、下载并安装后续版本。学习记录和草稿会保留。</p><pre>'+html.escape(record['notes'])+'</pre><p>SHA-256：<code>'+setup['sha256']+'</code></p></html>', encoding='utf8')
    remote(f'mkdir -p {REMOTE}/assets/{version} {REMOTE}/stable')
    for path in assets:
        target = f'{REMOTE}/assets/{version}/{path.name}'
        present = remote(f'if test -f {target}; then sha256sum {target}; fi').split()
        if not present or present[0] != sha(path):
            print('Uploading', path.name, path.stat().st_size, flush=True)
            upload(path, target+'.upload')
            actual = remote(f'sha256sum {target}.upload').split()[0]
            if actual != sha(path): raise ValueError('Uploaded asset checksum differs')
            remote(f'mv {target}.upload {target}')
    # Use the already persistent config volume; reload Caddy without recreating
    # the API, database, Redis, containers or any existing personal data.
    remote(f'docker exec {CONTAINER} mkdir -p /config/tb-updates/assets /config/tb-updates/stable\ndocker cp {REMOTE}/assets/{version} {CONTAINER}:/config/tb-updates/assets/')
    for asset in record['assets']:
        actual = remote(f'docker exec {CONTAINER} sha256sum /config/tb-updates/assets/{version}/{asset["name"]}').split()[0]
        if actual != asset['sha256']: raise ValueError('Served asset checksum differs')
    candidate = '/opt/tb-leaderboard/Caddyfile.updates-next'
    upload(ROOT/'server/leaderboard/Caddyfile', candidate)
    remote(f'docker cp {candidate} {CONTAINER}:/tmp/Caddyfile.updates-next\ndocker exec {CONTAINER} caddy validate --config /tmp/Caddyfile.updates-next --adapter caddyfile')
    backup = '/opt/tb-leaderboard/Caddyfile.before-updates-'+datetime.now().strftime('%Y%m%d-%H%M%S')
    try:
        remote(f'cp /opt/tb-leaderboard/Caddyfile {backup}\ncat {candidate} > /opt/tb-leaderboard/Caddyfile\ndocker exec {CONTAINER} caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile')
    except Exception:
        remote(f'cat {backup} > /opt/tb-leaderboard/Caddyfile\ndocker exec {CONTAINER} caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile')
        raise
    for local, name in ((page,page.name), (page,'index.html'), (metadata,'manifest-v1.json')):
        upload(local, REMOTE+'/stable/'+name+'.next')
        remote(f'docker cp {REMOTE}/stable/{name}.next {CONTAINER}:/config/tb-updates/stable/{name}.next\ndocker exec {CONTAINER} mv /config/tb-updates/stable/{name}.next /config/tb-updates/stable/{name}\nmv {REMOTE}/stable/{name}.next {REMOTE}/stable/{name}')
    (args.work/'published.json').write_text(json.dumps({'version': version, 'commit': commit, 'feed': BASE+'/stable/manifest-v1.json', 'assets': record['assets']}, indent=2)+'\n', encoding='utf8')
    print('Published', version, BASE+'/stable/index.html', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--key', required=True, type=Path)
    parser.add_argument('--notes', required=True, type=Path)
    parser.add_argument('--work', required=True, type=Path)
    publish(parser.parse_args())
