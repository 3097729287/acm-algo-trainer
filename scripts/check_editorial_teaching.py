"""Verify reference preservation, portable figures, links and teaching examples."""
import argparse
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re
import shutil
import subprocess
import tempfile

from refresh_editorial_teaching import ROOT, SOURCE, DOCS, reference_programs, selected_lessons, START


def load(p):return json.loads(p.read_text(encoding='utf-8'))


def check_preservation():
    # Earliest applied snapshot is the original public source, including changes
    # already present before this task. Do not compare against git HEAD instead.
    snapshots=sorted(p for p in (ROOT/'.backups').glob('editorial-teaching-*') if (p/'report.json').is_file())
    assert snapshots
    baseline=snapshots[0]/'before'
    public_folder=next(p.parent for p in baseline.rglob('solutions.json'))
    counts=Counter()
    lectures=load(SOURCE/'lectures.json');ids={row['id'] for row in lectures}
    problems={row['id']:row['encoded'] for row in load(SOURCE/'problems.json')}
    old_lectures={row['id']:row for row in load(public_folder/'lectures.json')}
    current_lectures={row['id']:row for row in lectures}
    for identity,row in old_lectures.items():assert current_lectures[identity]==row,identity
    links={(row['problem_id'],row['lecture_id']) for row in load(SOURCE/'links.json')}
    for row in load(public_folder/'links.json'):assert (row['problem_id'],row['lecture_id']) in links
    for variant in ['solutions','detailed_solutions']:
        old={row['problem_id']:row for row in load(public_folder/(variant+'.json'))}
        for row in load(SOURCE/(variant+'.json')):
            identity=row['problem_id'];previous=old[identity]
            assert reference_programs(row['markdown'])==reference_programs(previous['markdown']),identity
            for key,value in previous['images'].items():assert row['images'][key]==value,identity+' '+key
            assert row['markdown'].count(START)==1,identity
            assert '### 从零讲：' in row['markdown'],identity
            for name in selected_lessons(previous,problems[identity]):assert (identity,'lecture:foundation-'+name) in links,(identity,name)
            for target in re.findall(r'!\[[^]]*\]\(([^)]+)\)',row['markdown']):
                if target.startswith(('https:','http:','data:')):continue
                assert target in row['images'],(identity,target)
                assert base64.b64decode(row['images'][target].split(',',1)[1],validate=True)
                counts['imageReferences']+=1
            counts['publicArticles']+=1
    for path in baseline.rglob('*题解.md'):
        # Archive snapshots use the DSH directory mirror convention.
        mirror=path.parent.name
        if not mirror.startswith('D_Data_Code_题解'):continue
        source=Path('D:/Data/Code/题解')/mirror.removeprefix('D_Data_Code_题解_').replace('_','/')/path.name
        assert source.is_file(),source
        old=path.read_text(encoding='utf-8-sig');new=source.read_text(encoding='utf-8-sig')
        # Compare all original cpp blocks, including annotated excerpts.
        cpp=lambda t:re.findall(r'^```(?:cpp|c\+\+)\s*\n(.*?)^```\s*$',t,re.S|re.M)
        assert cpp(old)==cpp(new),source
        counts['archiveFiles']+=1
    return dict(counts)


def check_cpp():
    def snippets(name):return re.findall(r'```cpp\n(.*?)```',(DOCS/(name+'.md')).read_text(encoding='utf-8'),re.S)
    first_ge=snippets('bounds')[1]
    first_gt=first_ge.replace('first_ge','first_gt').replace('a[mid] < x','a[mid] <= x')
    definitions='\n'.join([first_ge,first_gt,snippets('modular')[0],snippets('number-theory')[0],snippets('dsu')[0]])
    body=r'''
    int assertions = 0;
    mt19937 rng(20261022);
    for (int n=0;n<=100;++n) {
        vector<int> a(n);
        for (int& x:a) x=int(rng()%13)-3;
        sort(a.begin(),a.end());
        for (int x=-5;x<=15;++x) {
            int lo=first_ge(a,x),hi=first_gt(a,x);
            assert(lo==count_if(a.begin(),a.end(),[&](int y){return y<x;}));
            assert(hi==count_if(a.begin(),a.end(),[&](int y){return y<=x;}));
            assert(hi-lo==count(a.begin(),a.end(),x));assertions+=3;
        }
    }
    for (long long mod=1;mod<32;++mod)
      for (long long a=-20;a<=20;++a)
        for(int e=0;e<12;++e) {
            long long brute=1%mod,base=(a%mod+mod)%mod;
            for(int k=0;k<e;++k)brute=brute*base%mod;
            assert(power(a,e,mod)==brute);++assertions;
        }
    for (int n=1;n<=1000;++n) {
        long long product=1;
        for(auto [p,e]:factor(n))for(int i=0;i<e;++i)product*=p;
        assert(product==n);++assertions;
    }
    DSU dsu(5);assert(dsu.merge(0,1));assert(dsu.merge(1,2));
    assert(!dsu.merge(0,2));assert(dsu.find(0)==dsu.find(2));assert(dsu.find(3)!=dsu.find(2));assertions+=5;
'''
    for name,selector,extra in [
        ('lambda',0,'assert(answer==5); ++assertions;'),
        ('lambda',1,'assert(a); ++assertions;'),
        ('lambda',2,'assert(a==11 && b==21); ++assertions;'),
        ('lambda',4,'assert(value==120); ++assertions;'),
        ('bindings',0,'assert(point.first==7 && x==9); ++assertions;'),
        ('numeric-tools',0,'assert(id==vector<int>({0,1,2,3}) && sum==3000000000LL && best==7); ++assertions;')]:
        body+='\n{\n'+snippets(name)[selector]+'\n'+extra+'\n}\n'
    source='#include <bits/stdc++.h>\n#include <cassert>\nusing namespace std;\n'+definitions+'\nint main(){\n'+body+'\ncout << assertions << " assertions passed\\n";\n}\n'
    compiler=shutil.which('g++');assert compiler
    with tempfile.TemporaryDirectory(prefix='tb-foundation-cpp-') as folder:
        here=Path(folder);(here/'checks.cpp').write_text(source,encoding='utf-8')
        compile=subprocess.run([compiler,'-std=c++17','-O2','checks.cpp','-o','checks.exe'],cwd=here,capture_output=True,text=True)
        assert compile.returncode==0,compile.stderr
        result=subprocess.run([str(here/'checks.exe')],cwd=here,capture_output=True,text=True,timeout=20)
        assert result.returncode==0,result.stderr
        output=result.stdout.strip()
        # The actual reference program receives independent closed-interval cases.
        article=next(r for r in load(SOURCE/'solutions.json') if r['problem_id']=='remote:nowcoder:141877::C')
        (here/'corridor.cpp').write_text(reference_programs(article['markdown'])[0],encoding='utf-8')
        compile=subprocess.run([compiler,'-std=c++17','-O2','corridor.cpp','-o','corridor.exe'],cwd=here,capture_output=True,text=True)
        assert compile.returncode==0,compile.stderr
        rng=random.Random(20261022)
        edges=[([(5,5)],0), ([(5,5)]*4,1), ([(1,5),(5,9),(5,5)],1), ([(1,10**9),(10**9,10**9)],0)]
        cases=list(edges)
        for _ in range(350):
            intervals=[]
            for _ in range(rng.randint(1,30)):
                l,r=sorted([rng.randint(1,15),rng.randint(1,15)]);intervals.append((l,r))
            cases.append((intervals,rng.randint(0,len(intervals))))
        for intervals,p in cases:
            cover=lambda x:sum(l<=x<=r for l,r in intervals)
            expected=sum(abs(cover(l)-cover(r))>=p for l,r in intervals)
            inp=f'{len(intervals)} {p}\n'+''.join(f'{l} {r}\n' for l,r in intervals)
            result=subprocess.run([str(here/'corridor.exe')],input=inp,cwd=here,capture_output=True,text=True,timeout=3)
            assert result.returncode==0 and result.stdout.strip()==str(expected),(intervals,p,result.stdout,expected)
    return {'cppExamples':output,'corridorCases':len(cases)}


if __name__=='__main__':
    print(json.dumps({'preservation':check_preservation(),'executed':check_cpp()},ensure_ascii=False,indent=2))
