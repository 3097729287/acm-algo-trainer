"""Compile the exact displayed guided references; verify independent small cases.

Keep generated evidence in the owned .backups tree for system-bin retirement.
No official judge submissions or user databases are involved.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
from itertools import permutations
import json
from pathlib import Path
import random
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def independent_cases(pid):
    rng=random.Random('guided-150-'+pid)
    if pid=='P8873':
        sequence=[]
        for wave in range(20):
            sequence+=list(range(wave+1))+list(range(wave-1,-wave-1,-1))+list(range(1-wave,1)) if wave else [0]
        return [(str(len(sequence))+'\n'+'\n'.join(str(i+1) for i in range(len(sequence)))+'\n',
                 '\n'.join(map(str,sequence)))]
    result=[]
    for number in range(70):
        n=rng.randrange(1,9);a=[rng.randrange(-10,11) for _ in range(n)]
        if pid=='P2249':
            a.sort();q=list(range(-12,13));inp=f'{n} {len(q)}\n'+' '.join(map(str,a))+'\n'+' '.join(map(str,q))
            expected=[a.index(x)+1 if x in a else -1 for x in q]
        elif pid=='B3691':
            a=[rng.randrange(1,12) for _ in a];cuts=[rng.randrange(1,12) for _ in range(rng.randrange(1,9))]
            inside=False;answer=0
            for x in a:
                keep=x not in set(cuts)
                if keep and not inside:answer+=1
                inside=keep
            inp=f'{n} {len(cuts)}\n'+' '.join(map(str,a))+'\n'+' '.join(map(str,cuts));expected=[answer]
        elif pid=='P1678':
            a=[rng.randrange(30) for _ in a];students=[rng.randrange(30) for _ in range(7)]
            inp=f'{n} 7\n'+' '.join(map(str,a))+'\n'+' '.join(map(str,students));expected=[sum(min(abs(x-y) for y in a) for x in students)]
        elif pid=='P2920':
            jobs=[(rng.randrange(1,8),rng.randrange(1,30)) for _ in range(min(n,6))]
            best=-10**9
            for order in permutations(jobs):
                elapsed=0;slack=10**9
                for length,deadline in order:elapsed+=length;slack=min(slack,deadline-elapsed)
                best=max(best,slack)
            inp=str(len(jobs))+'\n'+'\n'.join(f'{length} {deadline}' for length,deadline in jobs);expected=[best if best>=0 else -1]
        else:
            width=rng.randrange(1,n+1)
            inp=f'{n} {width}\n'+' '.join(map(str,a))
            if pid in {'P1886','P2251'}:
                expected=[min(a[i:i+width]) for i in range(n-width+1)]
                if pid=='P1886':expected +=[max(a[i:i+width]) for i in range(n-width+1)]
            elif pid=='P1440':expected=[min(a[max(0,i-width):i]) if i else 0 for i in range(n)]
            elif pid=='P1714':expected=[max(sum(a[i:j]) for i in range(n) for j in range(i+1,min(n,i+width)+1))]
            elif pid=='CF547B':
                a=[x+11 for x in a]
                inp=f'{n}\n'+' '.join(map(str,a))
                expected=[max(min(a[i:i+k]) for i in range(n-k+1)) for k in range(1,n+1)]
            else:raise ValueError(pid)
        result.append((inp+'\n',' '.join(map(str,expected))))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir',type=Path,required=True)
    args=parser.parse_args();work=args.work_dir.resolve()
    assert work.is_relative_to((ROOT/'.backups').resolve())
    work.mkdir(parents=True,exist_ok=False)
    compiler=shutil.which('g++');assert compiler
    guided=json.loads((ROOT/'backend/resources/template-guided.json').read_text('utf8'))
    source=json.loads((ROOT/'backend/resources/template-teaching.json').read_text('utf8'))
    jobs=[]
    for tasks in guided.values():
        for task in tasks:
            code=task['referenceCode']
            assert hashlib.sha256(code.encode()).hexdigest()==task['programSha256']
            cases=[(s['input'],s['output']) for s in task['samples']]+independent_cases(task['pid'])
            jobs.append((task['pid'],code,cases))
    for template in source['templates']:
        for edition in ('teaching','contest'):
            code=template['code' if edition=='teaching' else 'contestCode']+'\n'+template['example' if edition=='teaching' else 'contestExample']
            jobs.append((template['id'].split(':')[1]+'-'+edition,code,[('','')]))
    def check(job):
        identity,code,cases=job;folder=work/identity;folder.mkdir();cpp=folder/'main.cpp';exe=folder/'main.exe'
        cpp.write_text(code,'utf8')
        compiled=subprocess.run([compiler,'-std=c++17','-O2','-Wall','-Wextra',str(cpp),'-o',str(exe)],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=90)
        (folder/'compile.log').write_text(compiled.stdout+compiled.stderr,'utf8')
        if compiled.returncode:return {'id':identity,'passed':False,'error':compiled.stderr[-2000:]}
        for number,(inp,expected) in enumerate(cases):
            ran=subprocess.run([str(exe)],input=inp,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=8)
            if ran.returncode or ran.stdout.split()!=expected.split():
                failure={'id':identity,'passed':False,'case':number,'input':inp,'expected':expected,'actual':ran.stdout,'stderr':ran.stderr}
                (folder/'failure.json').write_text(json.dumps(failure,ensure_ascii=False,indent=2),'utf8');return failure
        return {'id':identity,'passed':True,'cases':len(cases),'programSha256':hashlib.sha256(code.encode()).hexdigest()}
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(check,jobs))
    report={'passed':all(r['passed'] for r in results),'programs':len(results),'inputRuns':sum(r.get('cases',0) for r in results),'originalSubmissions':0,'results':results}
    (work/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({**{k:v for k,v in report.items() if k!='results'},'failures':[r for r in results if not r['passed']]},ensure_ascii=False,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
