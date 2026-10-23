"""Compile teaching/curated programs and compare with independent small oracles."""
from pathlib import Path
import itertools
import json
import os
import random
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / '.backups/sequence-lab-20261023/cpp'
OUT.mkdir(parents=True, exist_ok=True)
DATA = json.loads((OUT.parent / 'course-export.json').read_text(encoding='utf-8'))
RNG = random.Random(20261023)
COMPILER = shutil.which('g++')
if not COMPILER:
    raise RuntimeError('A real C++17 compiler is required')
ENV = dict(os.environ, TB_OFFLINE='1')
RUNS = {}


def compile_program(name, code):
    source = OUT / (name + '.cpp')
    executable = OUT / (name + '.exe')
    source.write_text(code, encoding='utf-8')
    result = subprocess.run([COMPILER, '-std=c++17', '-O2', '-Wall', '-Wextra', str(source), '-o', str(executable)], capture_output=True, text=True, env=ENV)
    if result.returncode:
        raise AssertionError(name + '\n' + result.stderr)
    return executable


def run(name, exe, text, expected):
    result = subprocess.run([str(exe)], input=text, capture_output=True, text=True, timeout=5, env=ENV)
    assert result.returncode == 0, (name, result.stderr)
    assert result.stdout.split() == str(expected).split(), (name, text, expected, result.stdout)
    RUNS[name] = RUNS.get(name, 0) + 1


for pid, code in DATA['references'].items():
    exe = compile_program(pid, code)
    for text, expected in DATA['samples'][pid]:
        run(pid, exe, text, expected)
    for trial in range(28):
        n = RNG.randint(1, 7)
        a = [RNG.randint(1, 12) for _ in range(n)]
        if pid == '363B':
            k = RNG.randint(1, n)
            best = min(range(n-k+1), key=lambda l: sum(a[l:l+k])) + 1
            text = f'{n} {k}\n' + ' '.join(map(str, a))
            run(pid, exe, text, best)
        elif pid == '433B':
            b = sorted(a); queries = [(RNG.randint(1, 2), *sorted([RNG.randint(1,n), RNG.randint(1,n)])) for _ in range(8)]
            expected = [sum((a if t == 1 else b)[l-1:r]) for t,l,r in queries]
            text = f'{n}\n'+' '.join(map(str,a))+'\n8\n'+'\n'.join(f'{t} {l} {r}' for t,l,r in queries)
            run(pid, exe, text, ' '.join(map(str, expected)))
        elif pid == '816B':
            recipes = [sorted([RNG.randint(1, 12), RNG.randint(1, 12)]) for _ in range(n)]
            k = RNG.randint(1, n); queries = [sorted([RNG.randint(1, 15), RNG.randint(1, 15)]) for _ in range(6)]
            expected = [sum(sum(l <= t <= r for l,r in recipes) >= k for t in range(x,y+1)) for x,y in queries]
            text = f'{n} {k} 6\n'+'\n'.join(f'{l} {r}' for l,r in recipes+queries)
            run(pid, exe, text, ' '.join(map(str,expected)))
        elif pid == '295A':
            m,k = RNG.randint(1,7),RNG.randint(1,7)
            operations = [(*sorted([RNG.randint(1,n),RNG.randint(1,n)]),RNG.randint(0,7)) for _ in range(m)]
            commands = [sorted([RNG.randint(1,m),RNG.randint(1,m)]) for _ in range(k)]
            expected = a[:]
            for x,y in commands:
                for l,r,d in operations[x-1:y]:
                    for i in range(l-1,r): expected[i] += d
            text=f'{n} {m} {k}\n'+' '.join(map(str,a))+'\n'+'\n'.join(f'{l} {r} {d}' for l,r,d in operations)+'\n'+'\n'.join(f'{x} {y}' for x,y in commands)
            run(pid, exe, text, ' '.join(map(str,expected)))
        elif pid == '276C':
            q=RNG.randint(1,7);queries=[sorted([RNG.randint(1,n),RNG.randint(1,n)]) for _ in range(q)]
            expected=max(sum(sum(p[l-1:r]) for l,r in queries) for p in set(itertools.permutations(a)))
            text=f'{n} {q}\n'+' '.join(map(str,a))+'\n'+'\n'.join(f'{l} {r}' for l,r in queries)
            run(pid, exe, text, expected)
        elif pid == '381A':
            a=RNG.sample(range(1,100),n);remaining=a[:];score=[0,0];turn=0
            while remaining:
                score[turn]+=remaining.pop(0 if remaining[0]>remaining[-1] else -1);turn=1-turn
            run(pid, exe, f'{n}\n'+' '.join(map(str,a)), ' '.join(map(str,score)))
        elif pid == '1538C':
            low,high=sorted([RNG.randint(1,20),RNG.randint(1,20)])
            expected=sum(low<=a[i]+a[j]<=high for i in range(n) for j in range(i+1,n))
            run(pid, exe, f'1\n{n} {low} {high}\n'+' '.join(map(str,a)), expected)
        elif pid == '279B':
            budget=RNG.randint(1,25);expected=max([0]+[r-l for l in range(n) for r in range(l+1,n+1) if sum(a[l:r])<=budget])
            run(pid, exe, f'{n} {budget}\n'+' '.join(map(str,a)), expected)
        elif pid == '580B':
            people=[(RNG.randint(0,10),RNG.randint(0,12)) for _ in range(n)];d=RNG.randint(1,10);expected=0
            for mask in range(1,1<<n):
                group=[p for i,p in enumerate(people) if mask>>i&1]
                if max(p[0] for p in group)-min(p[0] for p in group)<d: expected=max(expected,sum(p[1] for p in group))
            run(pid, exe, f'{n} {d}\n'+'\n'.join(f'{m} {s}' for m,s in people), expected)
        elif pid == '701C':
            text=''.join(RNG.choice('abAB') for _ in range(n));need=set(text)
            expected=min(r-l for l in range(n) for r in range(l+1,n+1) if set(text[l:r])==need)
            run(pid, exe, f'{n}\n{text}', expected)

for key,item in DATA['lessons'].items():
    name='lesson-'+key;exe=compile_program(name,item['code'])
    for trial in range(24):
        n=RNG.randint(1,10);a=[RNG.randint(-9,9) for _ in range(n)]
        if key=='prefix':
            queries=[sorted([RNG.randint(1,n),RNG.randint(1,n)]) for _ in range(6)]
            run(name,exe,f'{n} 6\n'+' '.join(map(str,a))+'\n'+'\n'.join(f'{l} {r}' for l,r in queries),' '.join(str(sum(a[l-1:r])) for l,r in queries))
        elif key=='difference':
            ops=[(*sorted([RNG.randint(1,n),RNG.randint(1,n)]),RNG.randint(-9,9)) for _ in range(6)];b=a[:]
            for l,r,k in ops:
                for i in range(l-1,r):b[i]+=k
            run(name,exe,f'{n} 6\n'+' '.join(map(str,a))+'\n'+'\n'.join(f'{l} {r} {k}' for l,r,k in ops),' '.join(map(str,b)))
        elif key=='plane':
            h,w=RNG.randint(1,5),RNG.randint(1,5);grid=[[RNG.randint(-9,9) for _ in range(w)] for _ in range(h)];queries=[];answers=[]
            for _ in range(6):
                x1,x2=sorted([RNG.randint(1,h),RNG.randint(1,h)]);y1,y2=sorted([RNG.randint(1,w),RNG.randint(1,w)]);queries.append((x1,y1,x2,y2));answers.append(sum(grid[i][j] for i in range(x1-1,x2) for j in range(y1-1,y2)))
            run(name,exe,f'{h} {w} 6\n'+'\n'.join(' '.join(map(str,row)) for row in grid)+'\n'+'\n'.join(' '.join(map(str,q)) for q in queries),' '.join(map(str,answers)))
        elif key=='pair':
            a.sort();target=RNG.randint(-15,15);exists=any(a[i]+a[j]==target for i in range(n) for j in range(i+1,n))
            run(name,exe,f'{n} {target}\n'+' '.join(map(str,a)),'YES' if exists else 'NO')
        elif key=='window':
            a=list(map(abs,a));target=RNG.randint(1,20);lens=[r-l for l in range(n) for r in range(l+1,n+1) if sum(a[l:r])>=target]
            run(name,exe,f'{n} {target}\n'+' '.join(map(str,a)),min(lens) if lens else 0)
        elif key=='unique':
            text=''.join(RNG.choice('abAB') for _ in range(n));expected=max(r-l for l in range(n) for r in range(l+1,n+1) if len(set(text[l:r]))==r-l)
            run(name,exe,text,expected)
        elif key=='compact':
            b=[x for x in a if x!=0];run(name,exe,f'{n}\n'+' '.join(map(str,a)),str(len(b))+'\n'+' '.join(map(str,b)))
        elif key=='exact':
            target=RNG.randint(-9,9);expected=sum(sum(a[l:r])==target for l in range(n) for r in range(l+1,n+1))
            run(name,exe,f'{n} {target}\n'+' '.join(map(str,a)),expected)

# Numeric boundaries which small enumeration cannot expose.
large=compile_program('overflow-stones',DATA['references']['433B'])
run('overflow-stones',large,'3\n1000000000 1000000000 1000000000\n1\n1 1 3\n',3000000000)
large=compile_program('overflow-pairs',DATA['references']['1538C'])
n=70000
run('overflow-pairs',large,f'1\n{n} 2 2\n'+'1 '*n,n*(n-1)//2)
report={'status':'passed','programs':len(DATA['references'])+len(DATA['lessons']),'compiledArtifacts':len(list(OUT.glob('*.exe'))),'executions':sum(RUNS.values()),'perProgram':RUNS,'officialSampleGroups':sum(map(len,DATA['samples'].values()))}
(OUT.parent/'cpp-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
