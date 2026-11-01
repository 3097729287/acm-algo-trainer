import sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.dsh/tools'))
from verify import main
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))

def gen(rng):
    if rng.randrange(2):
        q=''.join(rng.choice('sixabc') for _ in range(rng.randint(1,12)))
        chars=list(q+'six');rng.shuffle(chars);p=''.join(chars)
    else:
        p=''.join(rng.choice('sixabc') for _ in range(rng.randint(1,15)))
        q=''.join(rng.choice('sixabc') for _ in range(rng.randint(1,15)))
    return f'1\n{len(p)} {len(q)}\n{p}\n{q}\n'
EDGES=[('重新排列后留下目标','1\n6 3\nxsiaaa\naaa\n','YES\n'),
 ('目标字母有重复约分','1\n6 3\niixxss\nisx\n','YES\n'),
 ('分母有无法约掉的字母','1\n3 1\nsix\na\n','NO\n'),
 ('多余字母不能丢弃','1\n5 1\nsixab\na\n','NO\n'),
 ('长度差正确仍可能字母不对','1\n4 1\nssix\ni\n','NO\n'),
 ('两侧完全抵消','1\n1 1\na\na\n','NO\n'),
 ('最短完全不同','1\n1 1\na\nb\n','NO\n'),
 ('合法最大分子','1\n100 97\n'+'z'*97+'six\n'+'z'*97+'\n','YES\n')]
LIMITS=[('最大组数和字符串长度',lambda:'100\n'+'100 100\n'+'a'*100+'\n'+'a'*100+'\n'+('100 100\n'+'a'*100+'\n'+'a'*100+'\n')*99,1.0)]
ROUNDS=300

if __name__=='__main__':
    ok=main(solution=str(HERE/'a.cpp'),brute=str(HERE/'a_brute.cpp'),
        gen=gen,edges=EDGES,limits=LIMITS,rounds=ROUNDS,seed=227800,
        checker=None,log_file=str(HERE/'../../_work/logs/verify_a.log'))
    sys.exit(0 if ok else 1)
