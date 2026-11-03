"""Small offline checks for public roster identity and additive source imports."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.backups/next-local-dev-20261104/import-check' / str(uuid.uuid4())
os.environ['TB_OFFLINE'] = '1'
os.environ['TB_STATE_DIR'] = str(OUT / 'state')
spec = importlib.util.spec_from_file_location('nowcoder_import', ROOT / 'scripts/import_nowcoder_training.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def rejected(action):
    try:
        action()
    except ValueError:
        return
    raise AssertionError('Invalid evidence was accepted')


base = module.BASE
endpoint = base + '/acm/contest/problem-list?token=&id=10'
row = lambda n: {'problemId': n, 'title': '公开题目 ' + str(n), 'index': str(1000 + n)}
page = lambda n, rows: {'code': 0, 'data': {'data': rows, 'basicInfo': {'problemCount': 3, 'pageCount': 2, 'pageSize': 2, 'pageCurrent': n}}}


class Fake:
    def __init__(self):
        self.pages = {endpoint: page(0, [row(1), row(2)]), endpoint + '&page=2': page(2, [row(3)])}
        self.html = {base + '/acm/contest/10': '<title>公开练习</title>'}

    def json(self, url):
        return copy.deepcopy(self.pages[url])

    def text(self, url):
        return self.html[url]


fake = Fake()
roster = module.contest_list(fake, base + '/acm/contest/10')
assert roster['officialProblemCount'] == 3
assert [p['pid'] for p in roster['problems']] == ['NC1', 'NC2', 'NC3']
assert roster['problems'][2]['contestUrl'].endswith('/10/1003')
fake.pages[endpoint + '&page=2']['data']['data'] = [row(1)]
rejected(lambda: module.contest_list(fake, base + '/acm/contest/10'))
fake.pages[endpoint + '&page=2'] = page(2, [row(3)])
fake.pages[endpoint + '&page=2']['data']['basicInfo']['problemCount'] = 4
rejected(lambda: module.contest_list(fake, base + '/acm/contest/10'))

collection_url = base + '/acm/problem/collection/20'
fake.html[collection_url] = '''<title>公开集合</title><a href="/acm/problem/1">NC1</a><a href="/acm/problem/1" class="title">第一题</a><a href="?page=2">2</a><script>var x={pageInfo: {"pageCount":2,"pageSize":1,"totalCount":2,"pageCurrent":1}};</script>'''
fake.html[collection_url + '?page=2'] = '''<a href="/acm/problem/2" class="title">第二题</a><script>var x={pageInfo: {"pageCount":2,"pageSize":1,"totalCount":2,"pageCurrent":2}};</script>'''
collected = module.collection_list(fake, collection_url)
assert [p['pid'] for p in collected['problems']] == ['NC1', 'NC2']
assert collected['problems'][0]['sourceTitle'] == '第一题'
fake.html[collection_url + '?page=2'] = fake.html[collection_url + '?page=2'].replace('/problem/2', '/problem/1')
rejected(lambda: module.collection_list(fake, collection_url))

samples = '<div class="question-oi"><textarea data-clipboard-text-id="input1">  1 2\n</textarea><textarea data-clipboard-text-id="output1"> 3 \n</textarea></div>'
assert module.original_samples(samples) == [{'name': '样例 1', 'input': '  1 2', 'output': ' 3 '}]
rejected(lambda: module.original_samples(samples.replace('data-clipboard-text-id="output1"', 'data-clipboard-text-id="other"')))
rejected(lambda: module.original_samples(samples.replace('data-clipboard-text-id="output1"', 'data-clipboard-text-id="output2"')))
rejected(lambda: module.Client(OUT / 'http').bytes('https://example.org/private'))

source = OUT / 'public-text'
source.mkdir(parents=True)
existing = {'id': 'existing-original', 'url': base + '/acm/problem/1', 'raw': {'keep': True}, 'encoded': {'title': '保留已核验内容'}}
old_statement = {'id': 'existing-original', 'markdown': '保留的原题面', 'samples': []}
legacy = {'id': 'local-legacy', 'url': None, 'raw': {}, 'encoded': {'title': '保留无网址的旧内容'}}
module.dump(source / 'problems.json', [existing, legacy])
module.dump(source / 'training_lists.json', [{'id': 'unrelated-public-list', 'problems': [], 'title': '保留题单'}])
module.dump(source / 'statements.json', [{'problem_id': existing['id'], 'content': old_statement}])
value = {'schema': 1, 'collectedAt': '2026-11-04T00:00:00Z', 'errors': [], 'lists': [collected],
         'problems': {base + '/acm/problem/' + str(n): {'title': '新标题 ' + str(n), 'statement': {'id': 'nowcoder-global::' + str(n), 'markdown': '原题内容', 'samples': []}} for n in [1, 2]}}
result = module.apply(copy.deepcopy(value), source, OUT / 'before')
assert (result['addedProblems'], result['reusedProblems'], result['newStatements']) == (1, 1, 1)
assert json.loads((source / 'problems.json').read_text('utf-8'))[0] == existing
assert json.loads((source / 'problems.json').read_text('utf-8'))[1] == legacy
assert module.load_statements(source)[0]['content'] == old_statement
lists = json.loads((source / 'training_lists.json').read_text('utf-8'))
assert lists[0]['id'] == 'unrelated-public-list'
assert lists[1]['problems'][0]['problemId'] == 'existing-original'
before = {p.relative_to(source): p.read_bytes() for p in source.rglob('*.json')}
again = module.apply(copy.deepcopy(value), source, OUT / 'before-repeat')
assert (again['addedProblems'], again['newStatements']) == (0, 0)
assert before == {p.relative_to(source): p.read_bytes() for p in source.rglob('*.json')}
assert not list(OUT.rglob('*.sqlite3'))
module.dump(OUT / 'report.json', {'ok': True, 'checks': ['numeric practice slots and complete pagination', 'duplicate or changed pages rejected', 'collection title aliases and counts', 'original sample whitespace and pair integrity', 'public-host guard', 'canonical reuse', 'existing source and statements preserved', 'unrelated lists preserved', 'repeat import is byte-idempotent', 'no SQLite writes']})
print('PASS: public rosters, sample integrity, canonical reuse, existing content, repeat import; evidence: ' + str(OUT))
