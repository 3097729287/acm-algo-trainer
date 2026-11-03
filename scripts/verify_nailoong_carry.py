"""Recheck the delivered carry DP against independent legal operation trees.

Only the explicit disposable work directory is written. The published articles,
their extraction snapshots, and personal databases are never modified.
"""
import argparse
import base64
import datetime
import hashlib
import json
from pathlib import Path
import random
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
IDENTITY='月赛 304::B'


def oracle(x,y):
    results={y}
    while x:
        bit=x&-x;x-=bit
        results={value+bit for value in results}|{value|bit for value in results}
    return min(results)


def verify(folder,compiler=None):
    folder=folder.resolve()
    if not folder.is_relative_to((ROOT/'.backups').resolve()):raise ValueError('Use an isolated .backups work directory')
    folder.mkdir(parents=True,exist_ok=False)
    articles={name:next(row for row in json.loads((ROOT/'data/library'/f'{name}.json').read_text('utf-8'))
                       if row['problem_id']==IDENTITY) for name in ['solutions','detailed_solutions']}
    programs={name:re.findall(r'```cpp\n(.*?)```',row['markdown'],re.S) for name,row in articles.items()}
    assert all(len(code)==1 for code in programs.values())
    code=programs['solutions'][0];assert code==programs['detailed_solutions'][0]
    reference_sha=hashlib.sha256(code.encode()).hexdigest()
    assert reference_sha=='d6f9a7248c0b0d5a51b1d49ec654ff5033bb0bcb6afcc2019f68929f89b82f23'
    source=folder/'reference.cpp';source.write_text(code,'utf-8')
    compiler=compiler or shutil.which('g++')
    if not compiler:raise RuntimeError('A C++17 compiler is required')
    executable=folder/'reference.exe'
    subprocess.run([compiler,'-std=c++17','-O2',str(source),'-o',str(executable)],check=True,capture_output=True,timeout=60)
    cases=[(x,y) for x in range(256) for y in range(256)]
    boundary=[0,1,2,3,(1<<29)-1,1<<29,(1<<30)-2,(1<<30)-1]
    cases.extend((x,y) for x in boundary for y in boundary)
    rng=random.Random(0x17594)
    cases.extend((rng.randrange(1<<30),rng.randrange(1<<30)) for _ in range(1024))
    assert all(0<=x<1<<30 and 0<=y<1<<30 for x,y in cases)
    inputs=hashlib.sha256();outputs=hashlib.sha256();batches=0
    for start in range(0,len(cases),10000):
        part=cases[start:start+10000]
        raw=str(len(part))+'\n'+''.join(f'{x} {y}\n' for x,y in part)
        expected=[oracle(x,y) for x,y in part]
        received=subprocess.run([str(executable)],input=raw,text=True,capture_output=True,check=True,timeout=20)
        assert [int(line) for line in received.stdout.split()]==expected,'Reference differs from complete operation trees'
        inputs.update(raw.encode());outputs.update(received.stdout.encode());batches+=1
    # This known counterexample independently rejects the local OR-only greedy.
    assert oracle(3,5)==6 and (3|5)==7
    import sqlite3
    with sqlite3.connect((ROOT/'data/library.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as db:
        statement=json.loads(db.execute('SELECT content FROM statements WHERE problem_id=?',(IDENTITY,)).fetchone()[0])
    for sample in statement['samples']:
        result=subprocess.run([str(executable)],input=sample['input'],text=True,capture_output=True,check=True,timeout=20)
        assert result.stdout.split()==sample['output'].split()
    image=base64.b64decode(articles['detailed_solutions']['images']['assets/core7/P17594.svg'].split(',',1)[1])
    report={'problemId':IDENTITY,'sourceUrl':'https://www.luogu.com.cn/problem/P17594',
        'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'variants':{name:hashlib.sha256(row['markdown'].encode()).hexdigest() for name,row in articles.items()},
        'referenceSha256':reference_sha,'sharedCppUnchanged':True,
        'compiler':subprocess.check_output([compiler,'--version'],text=True).splitlines()[0],
        'independentOperationTreeCases':len(cases),'exhaustiveSmallCases':256**2,
        'boundaryAndDeterministicRandomCases':len(cases)-256**2,
        'actualReferenceProcesses':batches+len(statement['samples']),'maximumTPerGeneratedInput':10000,
        'allGeneratedInputsWithinFormalConstraints':True,'officialSamplesPassed':True,
        'orOnlyGreedyCounterexample':{'x':3,'y':5,'correct':6,'greedy':7},
        'generatedInputSha256':inputs.hexdigest(),'actualOutputSha256':outputs.hexdigest(),
        'currentFigureSha256':hashlib.sha256(image).hexdigest(),'officialSubmissionMade':False}
    (folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir',required=True,type=Path)
    parser.add_argument('--compiler')
    args=parser.parse_args();verify(args.work_dir,args.compiler)
