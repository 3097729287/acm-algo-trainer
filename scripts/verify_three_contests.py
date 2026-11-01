"""Generate per-task verify.py inputs and run independent local verification."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
from three_contests_programs import ARCHIVE, CONTENT, ROOT, ROUNDS, PROGRAMS

SPECS = {}

SPECS['week168','B'] = r'''
def gen(rng):
    n,m=rng.randint(1,9),rng.randint(1,9)
    return f'{n} {m}\n'+'\n'.join(''.join(rng.choice('.#') for _ in range(m)) for _ in range(n))+'\n'
EDGES=[('单格故障','1 1\n#\n','1\n'),('单列','4 1\n#\n.\n#\n#\n','3\n'),('内圈不计','3 3\n...\n.#.\n...\n','0\n')]
LIMITS=[('最大面积',lambda:'200 2000\n'+('#'*2000+'\n')*200,2.0)]
'''
SPECS['week168','C'] = r'''
def gen(rng):
    n=rng.randint(1,25)
    return f'{n} {rng.randint(1,20)}\n'+' '.join(str(rng.randint(-30,30)) for _ in range(n))+'\n'
EDGES=[('负数单点','1 7\n-5\n','1\n'),('模一','4 1\n-3 0 9 -7\n','4\n'),('同余负余数','3 5\n-1 5 4\n','1\n')]
LIMITS=[('最大规模正负交替',lambda:'200000 1000000000\n'+('1000000000 -1000000000 '*100000)+'\n',2.0)]
'''
SPECS['week168','D'] = r'''
def gen(rng):
    n=rng.randint(1,30);m=rng.randint(1,n)
    return f'{n} {m}\n'+' '.join(str(rng.randint(-100,100)) for _ in range(n))+'\n'+' '.join(str(rng.randint(0,1000000000)) for _ in range(m))+'\n'
EDGES=[('单格','1 1\n-7\n1000000000\n','-7 1\n'),('绕回首部','4 4\n1 2 3 4\n3 0 0 0\n','10 3\n'),('只移动一次','5 1\n1 2 3 4 5\n4\n','5 5\n')]
LIMITS=[('最大规模连续跳过',lambda:'200000 200000\n'+'1000000000 '*200000+'\n'+'0 '*200000+'\n',2.0)]
'''
STACK = r'''
def gen(rng):
    n,m=rng.randint(1,6),rng.randint(1,6);k=rng.randint(0,n+m)
    a=[(rng.randint(-20,20),rng.randint(0,1)) for _ in range(n+m)]
    return f'1\n{n} {m} {k}\n'+'\n'.join(f'{x} {flag}' for x,flag in a)+'\n'
EDGES=[('空方案','1\n1 1 0\n-9 1\n-8 1\n','0\n'),('不能停在零分','1\n1 1 1\n-9 1\n-8 1\n','-8\n'),('最后标记一不强迫多取','1\n1 1 2\n3 1\n5 1\n','8\n'),('强制换堆却已空','1\n3 1 4\n1 1\n1 1\n1 1\n1 1\n','IMPOSSIBLE\n'),('同堆零连续','1\n3 1 3\n10 0\n11 0\n12 1\n-100 1\n','33\n')]
'''
SPECS['week168','E'] = STACK + r'''
LIMITS=[('Easy 最大二维规模',lambda:'1\n2000 2000 2000\n'+('1000000000 0\n'*4000),2.0)]
'''
SPECS['week168','G'] = STACK + r'''
LIMITS=[('Hard 最大规模全一',lambda:'1\n200000 200000 400000\n'+('1000000000 1\n'*400000),2.0),('Hard 最大规模全负',lambda:'1\n200000 200000 200000\n'+('-1000000000 0\n'*400000),2.0)]
'''
SPECS['week168','F'] = r'''
def gen(rng):
    n=rng.randint(2,8)
    return f'1\n{n}\n'+' '.join(str(rng.randint(0,n)) for _ in range(n))+'\n'
EDGES=[('全部喝奶且恰好两人','1\n2\n0 0\n','2\n'),('全部不喝奶','1\n4\n4 4 4 4\n','0\n'),('三人都需喝奶','1\n3\n0 0 0\n','0\n'),('恰两名耐辣为零','1\n4\n0 0 4 4\n','24\n')]
LIMITS=[('最大规模阶梯阈值',lambda:'1\n400\n'+' '.join(str(i) for i in range(400))+'\n',2.0)]
'''
SPECS['abc482','B'] = r'''
def gen(rng):
    return '\n'.join(''.join(rng.choice('.o') for _ in range(5)) for _ in range(5))+'\n'
EDGES=[('全空',('.'*5+'\n')*5,'5\n'),('已有斜线','o....\n.o...\n..o..\n...o.\n....o\n','0\n'),('反斜线差一个','....o\n...o.\n.....\n.o...\no....\n','1\n')]
LIMITS=[('固定最大棋盘',lambda:('.'*5+'\n')*5,2.0)]
'''
SPECS['abc482','C'] = r'''
def gen(rng):
    h,w=rng.randint(1,10),rng.randint(1,10);n=rng.randint(1,min(h*w,25));q=rng.randint(1,30)
    points=rng.sample([(i,j) for i in range(1,h+1) for j in range(1,w+1)],n)
    queries=[]
    for _ in range(q):
        t=rng.randint(1,2);lo=rng.randint(1,h if t==1 else w);hi=rng.randint(lo,h if t==1 else w);queries.append(f'{t} {lo} {hi}')
    return f'{h} {w} {n} {q}\n'+'\n'.join(f'{i} {j}' for i,j in points)+'\n'+'\n'.join(queries)+'\n'
EDGES=[('唯一坐标','1 1 1 2\n1 1\n1 1 1\n2 1 1\n','1\n1\n'),('重复行与空区间','10 10 3 4\n2 1\n2 2\n8 3\n1 2 2\n1 3 7\n1 1 10\n2 1 2\n','2\n0\n3\n2\n')]
def large():
    n=300000
    return f'1000000000 1000000000 {n} {n}\n'+''.join(f'{i} {i}\n' for i in range(1,n+1))+'1 1 1000000000\n'*n
LIMITS=[('最大点数与查询数',large,2.0)]
'''
SPECS['abc482','D'] = r'''
def gen(rng):
    n=rng.randint(1,4);xs=sorted(rng.sample(range(5),n))
    xs=[2*(x-xs[0]) for x in xs]
    return str(n)+'\n'+' '.join(map(str,xs))+'\n'
EDGES=[('单人','1\n1000000000\n','0\n'),('两人','2\n0 10\n','5\n5\n'),('中间两侧同距','3\n0 2 4\n','2\n2\n2\n'),('明显不对称','4\n0 2 4 100\n','50\n49\n49\n50\n')]
LIMITS=[('最大人数',lambda:'200000\n'+' '.join(str(2*i) for i in range(200000))+'\n',2.0)]
'''
SPECS['abc482','E'] = r'''
def gen(rng):
    n=rng.randint(2,22);es=[(i,rng.randrange(1,i)) for i in range(2,n+1)]
    rng.shuffle(es)
    return str(n)+'\n'+'\n'.join(f'{i} {j}' for i,j in es)+'\n'+' '.join(str(rng.randint(1,n)) for _ in range(n))+'\n'
EDGES=[('两点同色','2\n1 2\n1 1\n','1\n'),('两点异色','2\n1 2\n1 2\n','0\n'),('单中心三个分支','4\n1 2\n1 3\n1 4\n1 2 2 2\n','3\n'),('双中心四对','6\n1 2\n1 3\n1 4\n2 5\n2 6\n1 1 2 2 2 2\n','4\n'),('同分支不能配','5\n1 2\n2 3\n2 4\n1 5\n1 1 2 2 3\n','0\n')]
def large(star):
    n=200000
    return str(n)+'\n'+''.join(f'{1 if star else i-1} {i}\n' for i in range(2,n+1))+'1 '*n+'\n'
LIMITS=[('最大链避免递归栈',lambda:large(False),2.0),('最大同色星形答案超 int',lambda:large(True),2.0)]
'''
SPECS['abc482','F'] = r'''
def gen(rng):
    return f'{rng.randint(1,30000)} {rng.randint(1,90)}\n'
EDGES=[('单位模数','1 1\n','1\n'),('N 为一','1 4\n','-1\n1\n-1\n-1\n'),('非互质有零余数','4 8\n','2\n1\n1\n-1\n1\n-1\n-1\n-1\n'),('起点正整数轮次','2 3\n','-1\n1\n1\n')]
LIMITS=[('大素数试除',lambda:'99999999999973 400000\n',2.0),('多因子与最大模数',lambda:'30425026352700 400000\n',2.0),('高重数',lambda:'70368744177664 400000\n',2.0)]
'''

def make_scripts():
    for idx, ((key,letter),body) in enumerate(SPECS.items()):
        platform,series,number,_,letters=ROUNDS[key]
        folder=ARCHIVE/platform/series/number/(letters[0]+'-'+letters[-1])/letter
        rounds=1000 if (key,letter) in {('week168','D'),('week168','E'),('week168','G'),('week168','F'),('abc482','E'),('abc482','F')} else 300
        code="import os, sys\nfrom pathlib import Path\nsys.path.insert(0, os.path.expanduser('~/.dsh/tools'))\nfrom verify import main\nHERE=Path(__file__).resolve().parent\n"+body+f'''
if __name__ == '__main__':
    ok=main(solution=str(HERE/'{letter.lower()}.cpp'),brute=str(HERE/'{letter.lower()}_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds={rounds},seed={26110200+idx},
        log_file=str(HERE/'../../_work/logs/verify_{letter.lower()}.log'))
    sys.exit(0 if ok else 1)
'''
        for target in [folder/f'verify_{letter.lower()}.py',CONTENT/key/'programs'/letter/f'verify_{letter.lower()}.py']:
            target.write_text(code,encoding='utf8',newline='\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--generate-only',action='store_true');ap.add_argument('--round');args=ap.parse_args()
    make_scripts()
    if args.generate_only:return
    results=[]
    for key,spec in ROUNDS.items():
        if args.round and key!=args.round:continue
        platform,series,number,_,letters=spec
        for letter in letters:
            folder=ARCHIVE/platform/series/number/(letters[0]+'-'+letters[-1])/letter
            task=folder/f'verify_{letter.lower()}.py'
            print('VERIFY',key,letter,flush=True)
            result=subprocess.run([sys.executable,str(task)],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=300)
            print(result.stdout[-2400:],flush=True)
            if result.stderr:print(result.stderr[-1800:],flush=True)
            results.append({'round':key,'letter':letter,'passed':result.returncode==0})
            if result.returncode:raise SystemExit(1)
    output=ROOT/'.backups/three-contests';output.mkdir(parents=True,exist_ok=True)
    (output/f'verification-{args.round or "all"}.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':main()
