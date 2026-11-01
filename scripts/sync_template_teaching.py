"""Build portable teaching supplements without altering original templates."""
import hashlib
import json
from pathlib import Path
import sys
from template_teaching_basics import VARIANTS, MIGRATIONS, MAX_WINDOW, additions, notes
from template_guided_basics import GUIDED

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / 'backend/resources/code-templates.json'
    templates = {x['id'].split(':', 1)[1]: x for x in json.loads(source.read_text('utf-8'))['templates']}
    statements = {x['problem_id']: x['content'] for x in json.loads((ROOT / 'data/library/statements.json').read_text('utf-8'))}
    from copy import deepcopy
    migrations = deepcopy(MIGRATIONS)
    migrations['window-extrema']['code'] = templates['window-extrema']['code'] + MAX_WINDOW + '''
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);int n,k;cin>>n>>k;
    vector<long long>a(n);for(auto&x:a)cin>>x;
    for(auto x:sliding_minimum(a,k))cout<<x<<' ';cout<<'\\n';
    for(auto x:sliding_maximum(a,k))cout<<x<<' ';cout<<'\\n';}
'''
    result = {'revision': '1.5.0-basic-variants-1', 'templates': additions(), 'topics': {}}
    for key, markdown in notes().items():
        migration = migrations[key]
        statement = statements[migration['problemId']]
        assert statement.get('samples') and statement.get('statementAvailable')
        migration.update(url=statement.get('url') or statement.get('sourceUrl'),
                         samples=statement['samples'], statementSha256=hashlib.sha256(statement['markdown'].encode()).hexdigest())
        assert migration['url'].startswith('https://')
        result['topics'][key] = {'markdown': markdown, 'variants': VARIANTS[key], 'migration': migration,
                                'learningPath': {'two-pointers': 'two-pointers', 'sliding-window': 'two-pointers',
                                                 'prefix-difference': 'prefix-difference'}.get(key, key)}
    target = ROOT / 'backend/resources/template-teaching.json'
    before = ROOT / '.backups/next-150/original/backend/resources/template-teaching.json'
    if target.exists() and not before.exists():
        before.parent.mkdir(parents=True, exist_ok=True)
        before.write_bytes(target.read_bytes())
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    from core7_import import reference_programs
    solutions={row['problem_id']:row for row in json.loads((ROOT/'data/library/solutions.json').read_text('utf-8'))}
    guided=deepcopy(GUIDED)
    for tasks in guided.values():
        assert len(tasks)==5
        for task in tasks:
            identity='luogu-training-'+task['pid']
            original=statements[identity]
            migration=next((item for item in migrations.values() if item['problemId']==identity and item.get('code')),None)
            programs=reference_programs(solutions[identity]['markdown']) if identity in solutions else [migration['code']] if migration else []
            assert len(programs)==1,identity
            task.update(problemId=identity,url=original.get('url') or original.get('sourceUrl'),
                        samples=original['samples'],statementSha256=hashlib.sha256(original['markdown'].encode()).hexdigest(),
                        referenceCode=programs[0],programSha256=hashlib.sha256(programs[0].encode()).hexdigest())
    (ROOT/'backend/resources/template-guided.json').write_text(json.dumps(guided,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'topics': len(result['topics']), 'addedTemplates': len(result['templates']),
                      'variants': sum(len(t['variants']) for t in result['topics'].values()),
                      'originalTemplateFileUnchanged': True, 'verificationStillRequired': True}))


if __name__ == '__main__':
    main()
