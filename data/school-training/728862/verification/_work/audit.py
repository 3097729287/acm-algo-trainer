"""Bounded exhaustive checks and rejection tests for the output validators."""
import concurrent.futures
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(HERE))
from validation import check_c,check_j,check_k

def run(letter,inp):
    p=ROOT/'A-L'/letter/(letter.lower()+'.exe')
    r=subprocess.run([str(p)],input=inp,text=True,capture_output=True,timeout=10)
    assert r.returncode==0,(letter,r.stderr)
    return r.stdout

def checks():
    totals={}
    # Enumerate every allocation, including unused operations, independently.
    cases=[];want=[]
    for a,b in itertools.product(range(1,6),repeat=2):
        for x,y in itertools.product(range(1,a+1),range(1,b+1)):
            for count in range(1,11):
                cases.append(f'{a} {b} {x} {y} {count}')
                want.append(min((a-da)*(b-db) for da in range(a-x+1) for db in range(b-y+1) if da+db<=count))
    got=list(map(int,run('D',str(len(cases))+'\n'+'\n'.join(cases)+'\n').split()))
    assert got==want;totals['D_allocations']=len(cases)
    # Direct divisor counting, without the prime-square theorem or primality sieve.
    values=list(range(1,10001))
    out=run('E',str(len(values))+'\n'+' '.join(map(str,values))+'\n').split()
    expected=[]
    for x in values:
        count=sum(1 if d*d==x else 2 for d in range(1,__import__('math').isqrt(x)+1) if x%d==0)
        expected.append('YES' if count==3 else 'NO')
    assert out==expected;totals['E_divisor_counts']=len(values)
    jobs=[]
    for n in range(1,21):
        for a,b,c in itertools.product(range(1,6),repeat=3):
            possibilities=[i+j+(n-i*a-j*b)//c for i in range(n//a+1) for j in range((n-i*a)//b+1) if (n-i*a-j*b)%c==0]
            if possibilities:jobs.append(('H',f'{n} {a} {b} {c}\n',str(max(possibilities))))
    for length in range(1,5):
        for a in itertools.product(range(1,4),repeat=length):
            for k in range(1,length+1):
                sums=[sum(a[l:l+k]) for l in range(length-k+1)]
                jobs.append(('C',f'{length} {k}\n'+ ' '.join(map(str,a))+'\n',str(sums.index(min(sums))+1)))
    def work(item):
        letter,inp,expected=item;actual=run(letter,inp)
        assert actual.strip()==expected,(letter,inp,actual,expected)
        return letter
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for letter in pool.map(work,jobs):totals[letter+'_exhaustive']=totals.get(letter+'_exhaustive',0)+1
    # All mixed simple graphs on three labelled vertices: missing, undirected,
    # forward directed or backward directed for each possible edge.
    inputs=[];want=[]
    for choices in itertools.product(range(4),repeat=3):
        edges=[]
        for (u,v),choice in zip([(1,2),(1,3),(2,3)],choices):
            if choice==1:edges.append((0,u,v))
            elif choice==2:edges.append((1,u,v))
            elif choice==3:edges.append((1,v,u))
        if not edges:continue
        feasible=any(all(not t or pos.index(u)<pos.index(v) for t,u,v in edges) for pos in itertools.permutations([1,2,3]))
        if feasible:
            pos=next(pos for pos in itertools.permutations([1,2,3]) if all(not t or pos.index(u)<pos.index(v) for t,u,v in edges))
            want.append('YES\n'+''.join(f'{u} {v}\n' if t or pos.index(u)<pos.index(v) else f'{v} {u}\n' for t,u,v in edges))
        else:want.append('NO\n')
        inputs.append(f'3 {len(edges)}\n'+''.join(f'{t} {u} {v}\n' for t,u,v in edges))
    inp=str(len(inputs))+'\n'+''.join(inputs);actual=run('K',inp)
    assert check_k(inp,actual,''.join(want)) is True;totals['K_mixed_graphs']=len(inputs)
    # Independent spanning-tree enumeration on three cities, not Prim/Kruskal.
    jt=[]
    for coords in itertools.product([(1,1),(2,1)],repeat=3):
        for c in itertools.product([1,3],repeat=3):
            k=[1,2,1];edges=[(i,3,c[i]) for i in range(3)]
            edges += [(i,j,(abs(coords[i][0]-coords[j][0])+abs(coords[i][1]-coords[j][1]))*(k[i]+k[j])) for i,j in itertools.combinations(range(3),2)]
            opt=10**9
            for tree in itertools.combinations(edges,3):
                g=[[] for _ in range(4)]
                for u,v,w in tree:g[u].append(v);g[v].append(u)
                reached={3};q=[3]
                for u in q:
                    for v in g[u]:
                        if v not in reached:reached.add(v);q.append(v)
                if len(reached)==4:opt=min(opt,sum(w for u,v,w in tree))
            inp='3\n'+''.join(f'{x} {y}\n' for x,y in coords)+' '.join(map(str,c))+'\n1 2 1\n'
            result=check_j(inp,run('J',inp),str(opt));assert result[0],result
            jt.append(inp)
    totals['J_all_spanning_trees']=len(jt)
    # Counterexamples deliberately reject invalid, expensive and incomplete answers.
    bad=[
      (check_c,('3 1\n1 5 9\n','3\n','1')),
      (check_j,('2\n1 1\n2 1\n1 1\n1 1\n','3\n2\n1 2\n0\n','2')),
      (check_j,('2\n1 1\n2 1\n1 1\n1 1\n','1\n1\n1\n0\n','2')),
      (check_k,('1\n2 1\n1 1 2\n','YES\n2 1\n','YES\n1 2\n')),
      (check_k,('1\n3 3\n0 1 2\n0 2 3\n0 1 3\n','YES\n1 2\n2 3\n3 1\n','YES\n1 2\n2 3\n1 3\n'))]
    for fn,args in bad:
        result=fn(*args);assert not(result[0] if isinstance(result,tuple) else result)
    totals['invalid_outputs_rejected']=len(bad)
    (HERE/'logs/bounded-audit.json').write_text(json.dumps(totals,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(totals,ensure_ascii=False))

if __name__=='__main__':checks()
