"""Check the individually authored traces, then run the original C++.

The full-library pass verifies preservation only. It never claims that the
other problems have been read or repaired.
"""
import base64
from collections import Counter
import itertools
import json
from pathlib import Path
import random
import shutil
import sqlite3
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from audit_editorial_reasoning import ROOT, SOURCE, reference_programs
from revise_editorial_reasoning import ECHO, SAVE, REVISED_IDS


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def brute(a):
    return [(l+1, r+1) for l in range(len(a)) for r in range(l+2, len(a))
            if a[l]*a[r] == sum(a[l+1:r])]


def trace(a):
    a = [0] + list(a)
    sums = list(itertools.accumulate(a))
    pos = {sums[i]: i for i in range(1, len(a))}
    events = []
    for r in range(3, len(a)):
        for value in range(1, 31):
            wanted = sums[r-1] - value * a[r]
            left = pos.get(wanted, -1) if wanted >= 0 else -1
            if wanted < 0:
                result = 'negative'
            elif wanted == 0:
                assert left == -1
                result = 'zero-is-not-a-left-endpoint'
            elif left < 1:
                result = 'missing-prefix'
            elif a[left] != value:
                result = 'guessed-value-does-not-match'
            else:
                result = 'accepted'
            if left >= 1:
                assert left <= r-2, 'Positive elements already guarantee the length check'
            events.append(dict(right=r, value=value, wanted=wanted, left=left, result=result))
    return events


def preservation():
    allowed = set(REVISED_IDS)
    merged = SAVE / 'merge-report.json'
    if merged.exists():
        report = load(merged)
        assert report.get('dryRun') is False
        for batch in report['packages']:
            package = load(ROOT / 'data/editorial-revisions' / (batch + '.json'))
            assert package['batch'] == batch
            allowed.update(item['problemId'] for item in package['problems'])
    articles = 0
    for variant in ['solutions', 'detailed_solutions']:
        previous = {r['problem_id']: r for r in load(SAVE/'before/data/library'/(variant+'.json'))}
        current = {r['problem_id']: r for r in load(SOURCE/(variant+'.json'))}
        assert previous.keys() == current.keys()
        for identity, old in previous.items():
            new = current[identity]
            assert reference_programs(new['markdown']) == reference_programs(old['markdown']), (variant, identity)
            for key, data in old['images'].items():
                assert new['images'][key] == data, (identity, key)
            if identity not in allowed:
                assert new == old, ('Unexpected unrelated revision', identity)
            articles += 1
    return articles


def run_cpp(cases):
    return run_reference(ECHO, [(str(len(array))+'\n'+' '.join(map(str,array))+'\n',expected) for array,expected in cases])


def run_reference(identity, cases):
    row = next(r for r in load(SOURCE/'solutions.json') if r['problem_id'] == identity)
    program = reference_programs(row['markdown'])
    assert len(program) == 1
    compiler = shutil.which('g++')
    assert compiler, 'g++ is required to check the original reference program'
    with tempfile.TemporaryDirectory(prefix='tb-echo-proof-') as temporary:
        work = Path(temporary)
        (work/'echo.cpp').write_text(program[0], encoding='utf-8')
        compiled = subprocess.run([compiler, '-std=c++17', '-O2', 'echo.cpp', '-o', 'echo.exe'], cwd=work, capture_output=True, text=True)
        assert compiled.returncode == 0, compiled.stderr
        for inp, expected in cases:
            result = subprocess.run([str(work/'echo.exe')], cwd=work, input=inp, capture_output=True, text=True, timeout=10)
            assert result.returncode == 0 and result.stdout.strip() == str(expected), (identity,inp[:250], expected, result.stdout, result.stderr)
    return len(cases)


def library_matches():
    count = 0
    with sqlite3.connect((ROOT/'data/library.sqlite3').as_uri()+'?mode=ro', uri=True) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        for key,value in load(SOURCE/'meta.json').items():
            assert db.execute('SELECT value FROM library_meta WHERE key=?',(key,)).fetchone()[0] == str(value),(key,value)
        for variant in ['solutions', 'detailed_solutions']:
            current = {r['problem_id']: r for r in load(SOURCE/(variant+'.json'))}
            rows = list(db.execute('SELECT problem_id,markdown,images FROM '+variant))
            assert len(rows) == len(current)
            for identity, markdown, images in rows:
                assert markdown == current[identity]['markdown']
                assert json.loads(images) == current[identity]['images']
                count += 1
    return count


def time_brute(n, edges, a, b, s, t):
    distances=[[0 if i==j else 10**6 for j in range(n)] for i in range(n)]
    neighbors=[[] for _ in range(n)]
    for u,v in edges:
        distances[u][v]=distances[v][u]=1
        neighbors[u].append(v);neighbors[v].append(u)
    for middle in range(n):
        for u in range(n):
            for v in range(n):
                distances[u][v]=min(distances[u][v],distances[u][middle]+distances[middle][v])
    weights=[abs(distances[a][u]-distances[b][u]) for u in range(n)]
    best=n
    def walk(u, used, peak):
        nonlocal best
        if u==t:
            best=min(best,peak)
            return
        for v in neighbors[u]:
            if not (used>>v)&1:
                walk(v,used|(1<<v),max(peak,weights[v]))
    walk(s,1<<s,weights[s])
    return best,weights


def orders_brute(a,b,budget):
    best=0
    for mask in range(1<<len(a)):
        if mask&(mask<<1) or mask.bit_count()%2:
            continue
        selected=[i for i in range(len(a)) if (mask>>i)&1]
        k=len(selected)//2
        cost=sum(a[i] for i in selected[:k])+sum(b[i] for i in selected[k:])
        if cost<=budget:
            best=max(best,k)
    return best


def adjacent_problem_checks():
    rng=random.Random(141877)
    source={row['problem_id']:row['content'] for row in load(SOURCE/'statements.json')}
    cases={letter:[] for letter in 'ABCDEF'}
    for letter in cases:
        for sample in source['remote:nowcoder:141877::'+letter]['samples']:
            cases[letter].append((sample['input']+'\n',sample['output'].strip()))
    cases['A'].append(('3 0\n1 0 3\n',-1))
    cases['B'].append(('10 3 2\n','3 33'))
    intervals=[(1,3),(2,4),(1,7),(3,5),(4,8),(5,6),(6,8),(7,9)]
    cover=lambda x:sum(l<=x<=r for l,r in intervals)
    endpoints=[(cover(l),cover(r)) for l,r in intervals]
    assert endpoints==[(2,4),(3,4),(2,4),(4,4),(4,3),(4,4),(4,3),(4,1)]
    assert [i for i,(l,r) in enumerate(intervals) if abs(cover(l)-cover(r))>=2]==[0,2,7]
    cases['C'].append(('8 2\n'+''.join(f'{l} {r}\n' for l,r in intervals),3))
    for _ in range(70):
        intervals=[tuple(sorted([rng.randint(1,15),rng.randint(1,15)])) for _ in range(rng.randint(1,20))]
        threshold=rng.randint(0,len(intervals))
        expected=sum(abs(cover(l)-cover(r))>=threshold for l,r in intervals)
        cases['C'].append((f'{len(intervals)} {threshold}\n'+''.join(f'{l} {r}\n' for l,r in intervals),expected))
    best,weights=time_brute(4,[(0,1),(1,2),(2,3),(3,0)],0,2,1,3)
    assert best==2 and weights==[2,0,2,0]
    for _ in range(150):
        n=rng.randint(2,7)
        edges={(rng.randrange(i),i) for i in range(1,n)}
        edges|={(i,j) for i in range(n) for j in range(i+1,n) if rng.randrange(4)==0}
        a,b=rng.sample(range(n),2);s=rng.randrange(n);t=rng.randrange(n)
        expected,_=time_brute(n,edges,a,b,s,t)
        cases['E'].append((f'{n} {len(edges)} {a+1} {b+1} {s+1} {t+1}\n'+''.join(f'{u+1} {v+1}\n' for u,v in edges),expected))
    a=[1,9,2,9,9,9,9];b=[9,9,9,9,2,9,1]
    assert orders_brute(a,b,6)==2 and orders_brute(a,b,5)==1
    for budget in [5,6]:
        cases['F'].append((f'7 {budget}\n'+' '.join(map(str,a))+'\n'+' '.join(map(str,b))+'\n',2 if budget==6 else 1))
    for _ in range(150):
        n=rng.randint(1,11);budget=rng.randint(0,80)
        a=[rng.randint(1,15) for _ in range(n)];b=[rng.randint(1,15) for _ in range(n)]
        expected=orders_brute(a,b,budget)
        cases['F'].append((f'{n} {budget}\n'+' '.join(map(str,a))+'\n'+' '.join(map(str,b))+'\n',expected))
    cases['F'].append(('4000 1000000000000000\n'+' '.join(['1000000000']*4000)+'\n'+' '.join(['1000000000']*4000)+'\n',1000))
    return {letter:run_reference('remote:nowcoder:141877::'+letter,rows) for letter,rows in cases.items()}


def main():
    example = [1, 2, 2, 1]
    events = trace(example)
    assert brute(example) == [(1, 3), (2, 4)]
    expected = {
        (3, 1): (1, 1, 'accepted'), (4, 1): (4, -1, 'missing-prefix'),
        (4, 2): (3, 2, 'accepted'), (4, 3): (2, -1, 'missing-prefix'),
        (4, 4): (1, 1, 'guessed-value-does-not-match'),
        (4, 5): (0, -1, 'zero-is-not-a-left-endpoint'), (4, 6): (-1, -1, 'negative')}
    for key, value in expected.items():
        event = next(e for e in events if (e['right'], e['value']) == key)
        assert (event['wanted'], event['left'], event['result']) == value
    exhaustive = 0
    branches = Counter()
    for size in range(3, 8):
        for array in itertools.product(range(1, 4), repeat=size):
            events = trace(array)
            answers = [(e['left'], e['right']) for e in events if e['result'] == 'accepted']
            assert len(answers) == len(set(answers)), 'No duplicate interval is counted'
            assert sorted(answers) == brute(array), array
            branches.update(e['result'] for e in events)
            exhaustive += 1
    cases = [(example, 2)]
    rng = random.Random(20261022)
    for _ in range(320):
        array = [rng.randint(1, 30) for _ in range(rng.randint(3, 40))]
        cases.append((array, len(brute(array))))
    for n in [3, 4, 31, 32, 33, 200000]:
        cases.append(([1]*n, n-2))
        cases.append(([30]*n, max(0, n-31)))
    figures = []
    figure_owners={'echo-interval.svg':ECHO,'echo-success.svg':ECHO,'echo-candidates.svg':ECHO,
                   'time-threshold.svg':'remote:nowcoder:141877::E',
                   'orders-split.svg':'remote:nowcoder:141877::F','orders-rolling.svg':'remote:nowcoder:141877::F'}
    for name,identity in figure_owners.items():
        path = ROOT/'docs/editorial-figures'/name
        data = path.read_bytes()
        ET.fromstring(data)
        for variant in ['solutions', 'detailed_solutions']:
            article = next(r for r in load(SOURCE/(variant+'.json')) if r['problem_id'] == identity)
            assert base64.b64decode(article['images']['assets/editorial-reasoning/'+name].split(',', 1)[1]) == data
        figures.append(name)
    report = dict(problemId=ECHO, preservedArticles=preservation(), sqliteMatchedArticles=library_matches(),
                  exhaustiveArrays=exhaustive, actualReferenceProgramCases=run_cpp(cases),
                  branchCoverage=dict(branches), figures=figures,
                  adjacentReferenceCases=adjacent_problem_checks(),
                  teachingReviewScope='Nowcoder 141877 A-F reviewed as one batch. Other inventory entries stay pending until individual review.')
    SAVE.mkdir(parents=True, exist_ok=True)
    (SAVE/'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
