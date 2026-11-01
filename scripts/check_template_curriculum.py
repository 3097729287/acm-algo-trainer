"""Execute both editions and original-problem transfers against small oracles.

Generated artifacts are retained under .backups for later system-bin recycling.
No personal state, official submissions or current installation is accessed.
"""
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations
import bisect
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.backups/next-150/template-programs'
HEAD='#include <bits/stdc++.h>\n#include <cassert>\nusing namespace std;\n'


def cases(kind):
    rng=random.Random(150010)
    result=[]
    for number in range(90):
        n=rng.randrange(0,9);a=[rng.randrange(0,6) for _ in range(n)]
        if kind in {'pair-count','unique','bounds'}:a=sorted(rng.randrange(-5,6) for _ in range(n))
        if kind=='last':
            lo,hi=sorted([rng.randrange(-30,31),rng.randrange(-30,31)]);target=rng.randrange(-40,41)
            found=[v for v in range(lo,hi) if v<=target]
            result.append((f'{lo} {hi} {target}\n',str(found[-1]) if found else 'none'));continue
        if kind=='rectangle':
            n=rng.randrange(1,5);m=rng.randrange(1,5);grid=[[rng.randrange(-9,10) for _ in range(m)] for _ in range(n)]
            x,u=sorted([rng.randrange(n+1),rng.randrange(n+1)]);y,v=sorted([rng.randrange(m+1),rng.randrange(m+1)])
            result.append((f'{n} {m}\n'+'\n'.join(' '.join(map(str,r)) for r in grid)+f'\n{x} {y} {u} {v}\n',str(sum(grid[i][j] for i in range(x,u) for j in range(y,v)))));continue
        target=rng.randrange(-3,15)
        if kind=='pair-count':expected=str(sum(a[i]+a[j]==target for i,j in combinations(range(n),2)))
        elif kind=='unique':
            selected=sorted(set(a));result.append((str(n)+'\n'+' '.join(map(str,a))+'\n',str(len(selected))+'\n'+' '.join(map(str,selected))));continue
        elif kind=='bounds':expected=f'{bisect.bisect_left(a,target)} {bisect.bisect_right(a,target)}'
        elif kind=='shortest':
            target=max(1,target);lengths=[j-i for i in range(n) for j in range(i+1,n+1) if sum(a[i:j])>=target]
            expected=str(min(lengths,default=0))
        elif kind=='count-windows':
            sums=[sum(a[i:j]) for i in range(n) for j in range(i+1,n+1)]
            expected=f'{sum(v<=target for v in sums)} {sum(v==target for v in sums)}'
        elif kind=='fixed':
            n=max(1,n);a=[rng.randrange(-9,10) for _ in range(n)];target=rng.randrange(1,n+1)
            value,index=min((sum(a[i:i+target]),i) for i in range(n-target+1));expected=f'{value} {index}'
        elif kind in {'maximum','earliest'}:
            a=[rng.randrange(-4,5) for _ in range(n)];target=rng.randrange(-1,n+3)
            values=[]
            if 1<=target<=n:
                for i in range(n-target+1):
                    part=a[i:i+target];values.append(max(part) if kind=='maximum' else i+part.index(min(part)))
            expected=' '.join(map(str,values))
        else:raise ValueError(kind)
        result.append((f'{n} {target}\n'+' '.join(map(str,a))+'\n',expected))
    if kind=='last':
        result += [('-9223372036854775808 -9223372036854775807 0\n','-9223372036854775808'),
                   ('-9223372036854775808 -9223372036854775808 0\n','none'),
                   ('9223372036854775806 9223372036854775807 9223372036854775807\n','9223372036854775806')]
    if kind=='pair-count':result += [('4 -1\n-9223372036854775808 -9223372036854775808 9223372036854775807 9223372036854775807\n','4')]
    return result


def transfers(kind):
    rng=random.Random(150011);result=[]
    for _ in range(45):
        n=rng.randrange(1,9)
        if kind=='friends':
            d=rng.randrange(1,10);friends=[(rng.randrange(20),rng.randrange(10)) for _ in range(n)]
            best=0
            for mask in range(1,1<<n):
                group=[friends[i] for i in range(n) if mask>>i&1]
                if max(p[0] for p in group)-min(p[0] for p in group)<d:best=max(best,sum(p[1] for p in group))
            inp=f'{n} {d}\n'+'\n'.join(f'{m} {s}' for m,s in friends);expected=str(best)
        elif kind=='books':
            a=[rng.randrange(1,10) for _ in range(n)];t=rng.randrange(1,30)
            best=max([0]+[j-i for i in range(n) for j in range(i+1,n+1) if sum(a[i:j])<=t])
            inp=f'{n} {t}\n'+' '.join(map(str,a));expected=str(best)
        elif kind=='lookup':
            a=sorted(rng.randrange(10) for _ in range(n));queries=[rng.randrange(12) for _ in range(7)]
            inp=f'{n} 7\n'+' '.join(map(str,a))+'\n'+' '.join(map(str,queries));expected=' '.join(str(a.index(q)+1 if q in a else -1) for q in queries)
        elif kind=='coffee':
            k=rng.randrange(1,n+1);intervals=[sorted([rng.randrange(1,16),rng.randrange(1,16)]) for _ in range(n)]
            queries=[sorted([rng.randrange(1,17),rng.randrange(1,17)]) for _ in range(6)]
            inp=f'{n} {k} 6\n'+'\n'.join(f'{l} {r}' for l,r in intervals+queries)
            expected='\n'.join(str(sum(sum(l<=t<=r for l,r in intervals)>=k for t in range(x,y+1))) for x,y in queries)
        elif kind=='extrema':
            a=[rng.randrange(-8,9) for _ in range(n)];k=rng.randrange(1,n+1)
            inp=f'{n} {k}\n'+' '.join(map(str,a));expected='\n'.join(' '.join(str(function(a[i:i+k])) for i in range(n-k+1)) for function in (min,max))
        else:raise ValueError(kind)
        result.append((inp+'\n',expected))
    if kind=='coffee':result.append(('2 1 2\n1 1\n200000 200000\n1 200000\n200000 200000\n','2\n1'))
    return result


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir',type=Path,default=WORK)
    args=parser.parse_args();work=args.work_dir.resolve()
    assert work.is_relative_to((ROOT/'.backups').resolve()),'Keep isolated artifacts in the owned workspace'
    source=json.loads((ROOT/'backend/resources/template-teaching.json').read_text('utf-8'))
    jobs=[]
    for key,lesson in source['topics'].items():
        for variant in lesson['variants']:
            tests=cases(variant['oracle'])
            for edition in ('code','contestCode'):
                jobs.append((key+'-'+variant['id']+'-'+edition,HEAD+variant[edition]+'\nint main(){'+variant['driver']+'}\n',tests,False))
        migration=lesson['migration'];samples=[(s['input'],s['output']) for s in migration['samples']]
        jobs.append((key+'-original-problem',migration['code'],samples+transfers(migration['oracle']),migration['oracle']=='extrema'))
    work.mkdir(parents=True,exist_ok=True)
    compiler=shutil.which('g++')
    assert compiler,'C++17 compiler required'
    def execute(job):
        identity,code,tests,two_lines=job;folder=work/identity
        folder.mkdir(exist_ok=False);cpp=folder/'a.cpp';exe=folder/'a.exe';cpp.write_text(code,'utf-8')
        compiled=subprocess.run([compiler,'-std=c++17','-O2','-Wall','-Wextra',str(cpp),'-o',str(exe)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
        (folder/'compile.log').write_text(compiled.stdout+compiled.stderr,'utf-8')
        if compiled.returncode:return {'id':identity,'passed':False,'phase':'compile','error':compiled.stderr[-2200:]}
        for number,(inp,expected) in enumerate(tests):
            result=subprocess.run([str(exe)],input=inp,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=4)
            same=result.stdout.split()==expected.split()
            if two_lines:same=same and len(result.stdout.strip().splitlines())==2
            if result.returncode or not same:
                failure={'id':identity,'passed':False,'case':number,'input':inp,'expected':expected,'actual':result.stdout,'error':result.stderr}
                (folder/'failure.json').write_text(json.dumps(failure,ensure_ascii=False,indent=2),'utf-8');return failure
        return {'id':identity,'passed':True,'cases':len(tests),'programSha256':hashlib.sha256(code.encode()).hexdigest()}
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(execute,jobs))
    report={'topics':len(source['topics']),'programs':len(results),'inputRuns':sum(r.get('cases',0) for r in results),'originalSubmissions':0,'passed':all(r['passed'] for r in results),'results':results}
    (work/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({**{k:v for k,v in report.items() if k!='results'},'failures':[r for r in results if not r['passed']]},ensure_ascii=False,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
