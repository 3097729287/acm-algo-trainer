"""Freeze the selected route and fetch missing public statements; no personal I/O."""
import json
import os
import re
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.backups/core7-editorials-20261030'
os.environ['TB_STATE_DIR'] = str(OUT / 'isolated-state')
os.environ['TB_OFFLINE'] = '1'
sys.path[:0] = [str(ROOT / 'backend/common'), str(ROOT / 'backend')]
from fetch_problem import LuoguSession, LG_SECTIONS
from statement_seed import load_statements


def main():
    source = ROOT / 'data/library'
    scope = json.loads((OUT / 'scope.json').read_text('utf-8'))
    known = {r['problem_id']: r['content'] for r in load_statements(source)}
    directory = OUT / 'statements'
    directory.mkdir(parents=True, exist_ok=True)
    session = LuoguSession(delay=1.5)
    failed = []
    for entry in scope:
        identity = entry['id']
        target = directory / (re.sub(r'[:<>/\\|?*]', '_', identity) + '.json')
        if target.exists():
            continue
        if identity in known:
            value = known[identity]
        else:
            try:
                pid = entry['url'].rstrip('/').split('/')[-1]
                raw = session.problem(pid)
                content = raw.get('content', {})
                markdown = '# ' + raw['name'] + '\n\n' + '\n\n'.join(
                    '## ' + title + '\n\n' + content[key] for key, title in LG_SECTIONS if content.get(key))
                value = {'id': identity, 'title': raw['name'], 'markdown': markdown, 'images': {},
                         'samples': [{'name': '样例 ' + str(i+1), 'input': sample[0], 'output': sample[1]}
                                     for i, sample in enumerate(raw.get('samples', []))],
                         'statementAvailable': True, 'sourceUrl': entry['url']}
            except Exception as error:
                failed.append({'id': identity, 'error': str(error)})
                print('FETCH FAILED', identity, str(error)[:160], flush=True)
                continue
            print('FETCHED', identity, len(value['samples']), flush=True)
        target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'collection-report.json').write_text(json.dumps({'scope': len(scope), 'cached': len(list(directory.glob('*.json'))), 'failed': failed}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
