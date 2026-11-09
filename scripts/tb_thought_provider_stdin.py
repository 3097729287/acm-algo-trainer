"""Explicit TB-only credential reuse. A reviewed SSH consumer receives stdin.

Default invocation reports field names only and does not decrypt or send a key.
The consumer argv JSON must contain no credentials. Never run a credential dump.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

TB_DOCUMENTS = Path('E:/\u9879\u76ee/ToBe/\u7248\u672c/\u6700\u65b0\u7248/\u7a0b\u5e8f/state/tb-documents.sqlite3')
FIELDS = ('PK_AI_ENDPOINT', 'PK_AI_MODEL', 'PK_AI_KEY')


def existing_tb_provider(*, decrypt=False):
    # Deliberately bypass ProviderSettings.credentials(): its legacy fallback
    # can read another project's .dsh credentials, outside this authorization.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
    from translation_config import _crypt, PROVIDERS, DEFAULT_DEEPSEEK_MODEL, normalize_base_url, valid_key
    with sqlite3.connect(TB_DOCUMENTS.as_uri() + '?mode=ro', uri=True) as db:
        db.execute('PRAGMA query_only=ON')
        row = db.execute('SELECT value FROM documents WHERE key=?', ('translation-settings.json',)).fetchone()
    if row is None:
        raise RuntimeError('TB_CONFIG_MISSING')
    value = json.loads(row[0])
    provider = value.get('provider')
    if provider not in PROVIDERS or not value.get('protectedKey'):
        raise RuntimeError('TB_CONFIG_MISSING')
    spec = PROVIDERS[provider]
    model = value.get('model') or spec['defaultModel']
    if provider == 'deepseek' and model in ('deepseek-chat', 'deepseek-reasoner'):
        model = DEFAULT_DEEPSEEK_MODEL
    endpoint = normalize_base_url(value.get('baseUrl', '') if provider == 'custom' else spec['baseUrl']) + '/chat/completions'
    result = {'provider': provider, 'endpoint': endpoint, 'model': model}
    if decrypt:
        key = _crypt(base64.b64decode(value['protectedKey']), True).decode()
        if not valid_key(key):
            raise RuntimeError('TB_CONFIG_KEY_INVALID')
        result['key'] = key
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ssh-argv', type=Path, help='Reviewed JSON argv beginning with ssh/ssh.exe; no secret arguments')
    parser.add_argument('--apply', action='store_true', help='Send only the three PK_AI fields to that reviewed SSH stdin consumer')
    args = parser.parse_args()
    try:
        if not args.apply:
            existing_tb_provider(decrypt=False)
            print(json.dumps({'status': 'inspection-only', 'targetFields': FIELDS, 'tbStoredProviderPresent': True,
                              'decrypted': False, 'sent': False, 'ordinaryConfigWritten': False}))
            return 0
        if args.ssh_argv is None or args.ssh_argv.stat().st_size > 16384:
            raise ValueError('SSH_CONSUMER_REQUIRED')
        argv = json.loads(args.ssh_argv.read_text(encoding='utf8'))
        if not isinstance(argv, list) or not 2 <= len(argv) <= 32 or not all(isinstance(v, str) and '\x00' not in v for v in argv):
            raise ValueError('SSH_ARGV_INVALID')
        if Path(argv[0]).name.lower() not in ('ssh', 'ssh.exe'):
            raise ValueError('SSH_CONSUMER_REQUIRED')
        config = existing_tb_provider(decrypt=True)
        payload = json.dumps(dict(zip(FIELDS, (config['endpoint'], config['model'], config['key'])))).encode()
        child_env = dict(os.environ)
        child_env.pop('NODE_DEBUG', None)
        # Capture both streams. A consumer must not echo credentials, but even
        # an erroneous echo is never forwarded into the calling tool's output.
        result = subprocess.run(argv, input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=60, env=child_env)
        config.clear()
        payload = b''
        print(json.dumps({'status': 'sent' if result.returncode == 0 else 'consumer-failed',
                          'targetFields': FIELDS, 'consumerExitCode': result.returncode,
                          'credentialValuesPrinted': False, 'ordinaryConfigWritten': False}))
        return 0 if result.returncode == 0 else 1
    except Exception as error:
        # Do not render exception text or captured subprocess output.
        print(json.dumps({'status': 'failed', 'errorType': type(error).__name__, 'credentialValuesPrinted': False}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
