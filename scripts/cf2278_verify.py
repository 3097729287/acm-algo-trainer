"""Generate standard verify.py drivers with original samples and exact oracles."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
from cf2278_programs import ROOT,CONTENT,ARCHIVE,OUT,LETTERS,put

CHECKER=r'''
from functools import lru_cache

def valid(inp,text):
    data=list(map(int,inp.split()));t=data[0]
    cases=[tuple(data[1+3*i:4+3*i]) for i in range(t)]
    lines=text.split()
    if len(lines)!=t:return False,'输出行数不对'
    moves='RSP'
    for counts,s in zip(cases,lines):
        if len(s)!=sum(counts) or any(c not in moves for c in s):return False,'长度或手势字符不合法'
        @lru_cache(None)
        def worst(x,y,z):
            i=len(s)-x-y-z
            if i==len(s):return 0
            best=10**9
            for a,left in enumerate((x,y,z)):
                if not left:continue
                rest=[x,y,z];rest[a]-=1
                b=moves.index(s[i]);score=0 if b==a else (1 if (b,a) in [(0,1),(1,2),(2,0)] else -1)
                best=min(best,score+worst(*rest))
            return best
        if worst(*counts)<0:return False,'存在 Alice 排列能使 Bob 输局更多'
    return True,''

def checker(inp,got,other):
    first=valid(inp,got)
    if not first[0]:return first
    if other:
        second=valid(inp,other)
        if not second[0]:return False,'独立基准或样例输出不合法：'+second[1]
    return True,''
'''

SPECS={
'B':r'''
from check_b import checker
def gen(rng):
    n=rng.randint(1,7);x=rng.randint(0,n);y=rng.randint(0,n-x);z=n-x-y
    return f'1\n{x} {y} {z}\n'
EDGES=[('只有石头','1\n1 0 0\n','P\n'),('三者并列','1\n1 1 1\n','PPP\n'),('两者并列且有零','1\n0 2 2\n','RRRR\n'),('只出布','1\n0 0 3\n','SSS\n')]
LIMITS=[('最大组数与最长输出',lambda:'1000\n'+'100 100 100\n'*1000,2.0)]
ROUNDS=300
''',
'C':r'''
def gen(rng):
    n=rng.randint(2,6)
    return f'1\n{n}\n'+' '.join(str(rng.randint(1,4)) for _ in range(n))+'\n'
EDGES=[('全一不可动','1\n4\n1 1 1 1\n','-1\n'),('只有一端活跃','1\n5\n4 1 1 1 1\n','4\n'),('两端活跃中间全一','1\n4\n2 1 1 3\n','4\n'),('内部活跃','1\n3\n1 2 1\n','3\n'),('最短两颗','1\n2\n6 7\n','12\n')]
LIMITS=[('最大总质量',lambda:'1\n200000\n'+'1000 '*200000+'\n',2.0),('最大长度仅端点活跃',lambda:'1\n200000\n2 '+'1 '*199999+'\n',2.0)]
ROUNDS=1000
''',
'D':r'''
def gen(rng):
    n=rng.randint(2,4)
    return f'1\n{n}\n'+' '.join(str(rng.randint(-2,2)) for _ in range(n))+'\n'
EDGES=[('全相等','1\n3\n-5 -5 -5\n','0 0\n'),('奇数中位数','1\n3\n1 2 3\n','2 2\n'),('偶数中间区间','1\n4\n0 0 10 10\n','20 10\n'),('极端值','1\n2\n-1000000000 1000000000\n','2000000000 2000000000\n'),('重复值','1\n4\n1 1 1 9\n','8 8\n')]
LIMITS=[('最大绝对成本',lambda:'1\n200000\n'+'-1000000000 '*100000+'1000000000 '*100000+'\n',2.0)]
ROUNDS=1000
''',
'E':r'''
def gen(rng):
    n=rng.randint(1,7)
    return f'1\n{n}\n'+' '.join(str(rng.randint(-4,4)) for _ in range(n))+'\n'
EDGES=[('负单点不允许变号','1\n1\n-3\n','-3\n'),('不能直接取绝对值','1\n2\n6 -7\n','1\n'),('含零奇数长度','1\n5\n-10 1 0 1 -10\n','18\n'),('全零','1\n4\n0 0 0 0\n','0\n'),('绝对值总和超 int','1\n4\n1000000000 -1000000000 1000000000 -1000000000\n','0\n')]
LIMITS=[('最大数量与边界值',lambda:'1\n200000\n'+('1000000000 -1000000000 '*100000)+'\n',2.0)]
ROUNDS=1000
''',
'F':r'''
def gen(rng):
    return f'1\n{rng.randint(2,7)} {rng.randint(1,7)}\n'
EDGES=[('长度二最小 m','1\n2 1\n','1\n'),('长度二无解','1\n2 2\n','0\n'),('唯一中间路径','1\n3 2\n','1\n'),('最后二或一','1\n3 1\n','3\n'),('一条路径多种停留','1\n4 1\n','6\n')]
LIMITS=[('最大二维状态',lambda:'1\n4000 4000\n',2.0),('组数上界与总和上界',lambda:'2000\n'+'2 2\n'*2000,2.0)]
ROUNDS=1000
''',
'G':r'''
def gen(rng):
    n=rng.randint(1,8);edges=[(i,rng.randrange(1,i)) for i in range(2,n+1)]
    x=''.join(rng.choice('01') for _ in range(n))
    if rng.randrange(2):
        children=[[] for _ in range(n)]
        for a,b in edges:children[b-1].append(a-1)
        y=list(x)
        for _ in range(rng.randrange(1<<n)):
            active=[0]
            for u in active:
                if y[u]=='0':y[u]='1'
                else:y[u]='0';active.extend(children[u])
        y=''.join(y)
    else:y=''.join(rng.choice('01') for _ in range(n))
    return f'1\n{n}\n'+''.join(f'{a} {b}\n' for a,b in edges)+x+'\n'+y+'\n'
EDGES=[('初态即终态','1\n1\n1\n1\n','0\n'),('单点从一到零','1\n1\n1\n0\n','1\n'),('同层矛盾','1\n3\n1 2\n1 3\n000\n010\n','-1\n'),('保留原不可达分支输入','1\n5\n1 2\n1 3\n2 4\n3 5\n01000\n00010\n','-1\n'),('不同分支进位不同','1\n5\n1 2\n1 3\n2 4\n3 5\n01000\n00110\n','2\n'),('三位进位','1\n3\n1 2\n2 3\n111\n000\n','1\n'),('超六十四位', '1\n66\n'+''.join(f'{i} {i+1}\n' for i in range(1,66))+'0'*66+'\n'+'0'*65+'1\n',str(pow(2,65,998244353))+'\n')]
def large(star):
    n=200000;es=''.join(f'{1 if star else i-1} {i}\n' for i in range(2,n+1))
    return '1\n'+str(n)+'\n'+es+'0'*n+'\n'+('0'+'1'*(n-1) if star else '0'*(n-1)+'1')+'\n'
LIMITS=[('最大深度与超大答案',lambda:large(False),2.0),('最大同层数量',lambda:large(True),2.0)]
ROUNDS=1000
''',
}

def generate():
    sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
    from statement_format import codeforces_samples
    samples=[]
    for letter in 'ABCDEFG':
        page=(ARCHIVE/'_work/raw'/(letter+'.html')).read_text('utf8')
        parsed=codeforces_samples(page)
        assert parsed,letter
        samples.extend((letter+' '+s['name'],s['input'],s['output']) for s in parsed)
    put(ARCHIVE/'_work/samples.py','# Official samples mechanically extracted from retained original pages.\nSAMPLES = '+repr(samples)+'\n')
    for letter in LETTERS:
        if letter=='B':
            for folder in [ARCHIVE/'B-G'/letter,CONTENT/'programs'/letter]:put(folder/'check_b.py',CHECKER.strip()+'\n')
        body="import sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path.home()/'.dsh/tools'))\nfrom verify import main\nHERE=Path(__file__).resolve().parent\nsys.path.insert(0,str(HERE))\n"+SPECS[letter]+f'''
if __name__=='__main__':
    ok=main(solution=str(HERE/'{letter.lower()}.cpp'),brute=str(HERE/'{letter.lower()}_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=ROUNDS,seed={227800+ord(letter)-65},
        checker={'checker' if letter=='B' else 'None'},log_file=str(HERE/'../../_work/logs/verify_{letter.lower()}.log'))
    sys.exit(0 if ok else 1)
'''
        for folder in [ARCHIVE/'B-G'/letter,CONTENT/'programs'/letter]:put(folder/f'verify_{letter.lower()}.py',body)
    print('Restored all seven official sample blocks mechanically, including the nested B sample.')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--letters',default=LETTERS);ap.add_argument('--generate-only',action='store_true');args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);generate()
    if args.generate_only:return
    results=[]
    for letter in args.letters:
        print('VERIFY',letter,flush=True)
        r=subprocess.run([sys.executable,str(ARCHIVE/'B-G'/letter/f'verify_{letter.lower()}.py')],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=300)
        print(r.stdout[-1800:],r.stderr[-800:],flush=True)
        results.append({'letter':letter,'passed':r.returncode==0})
        if r.returncode:raise SystemExit(1)
    (OUT/('verification-'+args.letters+'.json')).write_text(json.dumps(results,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':main()
