import sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))

def gen(rng):
    n=rng.randint(2,6)
    return f'1\n{n}\n'+' '.join(str(rng.randint(1,4)) for _ in range(n))+'\n'
EDGES=[('全一不可动','1\n4\n1 1 1 1\n','-1\n'),('只有一端活跃','1\n5\n4 1 1 1 1\n','4\n'),('两端活跃中间全一','1\n4\n2 1 1 3\n','4\n'),('内部活跃','1\n3\n1 2 1\n','3\n'),('最短两颗','1\n2\n6 7\n','12\n')]
LIMITS=[('最大总质量',lambda:'1\n200000\n'+'1000 '*200000+'\n',2.0),('最大长度仅端点活跃',lambda:'1\n200000\n2 '+'1 '*199999+'\n',2.0)]
ROUNDS=1000

if __name__=='__main__':
    ok=main(solution=str(HERE/'c.cpp'),brute=str(HERE/'c_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=ROUNDS,seed=227802,
        checker=None,log_file=str(HERE/'../../_work/logs/verify_c.log'))
    sys.exit(0 if ok else 1)
