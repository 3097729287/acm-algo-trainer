"""Compile the actual C++17 templates and compare to independent small oracles."""
import argparse
import itertools
import json
from pathlib import Path
import random
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def xors(values):
    result={0}
    for x in values: result |= {v^x for v in list(result)}
    return sorted(result)

def successor(nexts,v,k):
    seen={};path=[]
    while v not in seen:
        seen[v]=len(path);path.append(v);v=nexts[v]
    if k<len(path): return path[k]
    start=seen[v];return path[start+(k-start)%(len(path)-start)]

DRIVERS={
 'linear-basis':r'''int main(){int t;cin>>t;while(t--){int n,m;uint64_t seed,k;cin>>n>>m>>seed>>k;XorBasis b,c;for(int i=0;i<n;i++){uint64_t x;cin>>x;b.insert(x);}for(int i=0;i<m;i++){uint64_t x;cin>>x;c.insert(x);}auto kth=b.kth(k);auto nz=b.min_nonzero();cout<<b.rank<<' '<<b.max_xor(seed)<<' '<<b.min_xor(seed)<<' '<<b.contains(seed)<<' ';if(kth)cout<<*kth;else cout<<"none";cout<<' ';if(nz)cout<<*nz;else cout<<"none";b.merge(c);cout<<' '<<b.rank<<' '<<b.max_xor()<<'\n';}}''',
 'binary-lifting':r'''int main(){int t;cin>>t;while(t--){int n,q;cin>>n>>q;vector<int>a(n);for(int&x:a)cin>>x;BinaryLifting b(a);while(q--){int v;uint64_t k;cin>>v>>k;cout<<b.jump(v,k)<<' ';}cout<<'\n';}}''',
 'dinic':r'''int main(){int t;cin>>t;while(t--){int n,m;cin>>n>>m;Dinic f(n);while(m--){int u,v;long long c;cin>>u>>v>>c;f.add_edge(u,v,c);}cout<<f.max_flow(0,n-1)<<' '<<f.max_flow(0,n-1)<<' ';auto cut=f.source_side(0);for(bool b:cut)cout<<b;cout<<'\n';}}''',
 'li-chao':r'''void out(__int128_t x){if(x<0){cout<<'-';x=-x;}if(x>=10)out(x/10);cout<<int(x%10);}int main(){int t;cin>>t;while(t--){int n,m,q;cin>>n>>m>>q;vector<long long>xs(n);for(auto&x:xs)cin>>x;LiChao tree(xs);while(m--){long long k,b;cin>>k>>b;tree.add({k,b});}while(q--){long long x;cin>>x;auto y=tree.query(x);if(y)out(*y);else cout<<"none";cout<<' ';}cout<<'\n';}}'''
}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--compiler',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    rng=random.Random(20261030);jobs={};counts={}
    cases=[];expected=[]
    for i in range(500):
        n=rng.randrange(11);m=rng.randrange(4);a=[rng.getrandbits(64) if i%5==0 else rng.randrange(256) for _ in range(n)];b=[rng.randrange(256) for _ in range(m)]
        values=xors(a);merged=xors(a+b);seed=rng.getrandbits(64) if i%5==0 else rng.randrange(256);k=rng.randrange(len(values)+2)
        cases.append(f'{n} {m} {seed} {k}\n'+ ' '.join(map(str,a+b)))
        expected.append([str(len(values).bit_length()-1),str(max(v^seed for v in values)),str(min(v^seed for v in values)),str(int(seed in values)),str(values[k]) if k<len(values) else 'none',str(values[1]) if len(values)>1 else 'none',str(len(merged).bit_length()-1),str(merged[-1])])
    full=[1<<i for i in range(64)];cases.append('64 0 18446744073709551615 18446744073709551615\n'+' '.join(map(str,full)));expected.append(['64',str(2**64-1),'0','1',str(2**64-1),'1','64',str(2**64-1)])
    jobs['linear-basis']=(cases,expected)
    cases=[];expected=[]
    for i in range(150):
        n=rng.randrange(1,15);a=[rng.randrange(n) for _ in range(n)];queries=[(rng.randrange(n),rng.getrandbits(64) if j%3==0 else rng.randrange(1000)) for j in range(20)]
        cases.append(f'{n} {len(queries)}\n'+' '.join(map(str,a))+'\n'+'\n'.join(f'{v} {k}' for v,k in queries));expected.append([str(successor(a,v,k)) for v,k in queries])
    jobs['binary-lifting']=(cases,expected)
    cases=[];expected=[]
    for i in range(250):
        n=rng.randrange(2,8);edges=[(rng.randrange(n),rng.randrange(n),rng.randrange(8)) for _ in range(rng.randrange(20))]
        minimum=min(sum(c for u,v,c in edges if mask>>u&1 and not mask>>v&1) for mask in range(1<<n) if mask&1 and not mask>>(n-1)&1)
        cases.append(f'{n} {len(edges)}\n'+'\n'.join(f'{u} {v} {c}' for u,v,c in edges));expected.append((minimum,n,edges))
    jobs['dinic']=(cases,expected)
    cases=[];expected=[]
    for i in range(250):
        xs=[rng.randrange(-10,11) for _ in range(rng.randrange(12))];lines=[(rng.randrange(-20,21),rng.randrange(-30,31)) for _ in range(rng.randrange(12))]
        if i%5==0:lines +=[(10**18,-10**18),(-10**18,10**18)];xs +=[10**18,-10**18]
        query=xs+[1234567]
        cases.append(f'{len(xs)} {len(lines)} {len(query)}\n'+' '.join(map(str,xs))+'\n'+'\n'.join(f'{k} {b}' for k,b in lines)+'\n'+' '.join(map(str,query)))
        expected.append([str(min(k*x+b for k,b in lines)) if lines and x in xs else 'none' for x in query])
    jobs['li-chao']=(cases,expected)
    templates={t['id'].removeprefix('builtin:'):t for t in json.loads((ROOT/'backend/resources/code-templates.json').read_text(encoding='utf8'))['templates']}
    results=[]
    with tempfile.TemporaryDirectory(prefix='tobe-algorithm-operations-') as tmp:
        directory=Path(tmp)
        for key,(cases,expected) in jobs.items():
            for edition,field in [('teaching','code'),('contest','contestCode')]:
                code=templates[key][field];src=directory/f'{key}-{edition}.cpp';exe=src.with_suffix('.exe')
                src.write_text(code+'\n'+DRIVERS[key],encoding='utf8')
                built=subprocess.run([str(args.compiler),'-std=c++17','-O2','-Wall','-Wextra',str(src),'-o',str(exe)],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=120)
                assert built.returncode==0,built.stderr
                ran=subprocess.run([str(exe)],input=str(len(cases))+'\n'+'\n'.join(cases)+'\n',capture_output=True,text=True,timeout=30)
                assert ran.returncode==0,(key,ran.stderr)
                outputs=[line.split() for line in ran.stdout.splitlines()];assert len(outputs)==len(expected),(key,len(outputs),len(expected))
                for i,(actual,wanted) in enumerate(zip(outputs,expected)):
                    if key=='dinic':
                        minimum,n,edges=wanted;assert int(actual[0])==minimum and actual[1]=='0',(key,i,actual,wanted)
                        cut=actual[2];assert len(cut)==n and cut[0]=='1' and cut[-1]=='0'
                        assert sum(c for u,v,c in edges if cut[u]=='1' and cut[v]=='0')==minimum
                    else:assert actual==wanted,(key,edition,i,actual,wanted)
                # Compile and execute the exact minimal example shown beside each edition.
                src.write_text(code+'\n'+templates[key]['example' if edition=='teaching' else 'contestExample'],encoding='utf8')
                sample=subprocess.run([str(args.compiler),'-std=c++17','-O2',str(src),'-o',str(exe)],capture_output=True,text=True,timeout=120)
                assert sample.returncode==0,sample.stderr
                assert subprocess.run([str(exe)],capture_output=True,timeout=10).returncode==0,key
                results.append(dict(template=key,edition=edition,cases=len(cases),minimalExamplePassed=True))
    report=dict(ok=True,results=results,independentCases=sum(x['cases'] for x in results),compiledPrograms=len(results)*2,officialSubmissions=0)
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
