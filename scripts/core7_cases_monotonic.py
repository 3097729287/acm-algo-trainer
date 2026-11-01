from itertools import product
from functools import lru_cache
from collections import Counter
import random

IDS={'P10277', 'P7410', 'P9977', 'P5788', 'P1628', 'P15232', 'P1886', 'B3666', 'P2251', 'P2564', 'CF547B', 'UVA11462', 'CF1237D', 'P2947', 'P1950', 'P6503', 'P1440', 'UVA1619'}

def interviews(durations, k):
    states = {tuple(durations[:k])}
    for duration in durations[k:]:
        next_states = set()
        for state in states:
            for i, finish in enumerate(state):
                if finish == min(state):
                    nxt = list(state)
                    nxt[i] += duration
                    next_states.add(tuple(nxt))
        states = next_states
    starts = {min(s) for s in states}
    assert len(starts) == 1
    when = starts.pop()
    return str(when) + '\n' + ''.join((str(int(any((s[i] == when for s in states)))) for i in range(k)))

def road(cost, b):
    best = None
    for lanes in product(range(len(cost)), repeat=len(b)):
        count = Counter(lanes)
        if all((count[lanes[i]] <= b[i] for i in range(len(b)))):
            value = sum((cost[lane] for lane in lanes))
            best = value if best is None else min(best, value)
    return -1 if best is None else best

def towers(weights, m, k):
    weights = sorted(weights, reverse=True)

    @lru_cache(None)
    def visit(i, tops):
        if i == len(weights):
            return 0
        best = visit(i + 1, tops)
        for at, top in enumerate(tops):
            if top - weights[i] >= k:
                nxt = list(tops)
                nxt[at] = weights[i]
                best = max(best, 1 + visit(i + 1, tuple(sorted(nxt))))
        return best
    return visit(0, (10 ** 20,) * m)

def rectangle_count(matrix, predicate):
    h, w = (len(matrix), len(matrix[0]))
    answer = 0
    for top in range(h):
        for bottom in range(top, h):
            for left in range(w):
                for right in range(left, w):
                    answer += predicate([matrix[i][j] for i in range(top, bottom + 1) for j in range(left, right + 1)])
    return answer

def cases_for(pid):
    rng=random.Random(20261031);result=[]
    def put(inp,expected):result.append((f"独立校验 {len(result)+1}",str(inp),str(expected)))
    def row(values):return " ".join(map(str,values))+"\n"
    for test in range(180):
        if pid in ['P1440', 'P1886', 'P2251', 'P2947', 'P5788', 'B3666', 'UVA1619', 'P6503', 'CF547B', 'CF1237D']:
            n = rng.randint(2, 15)
            values = [rng.randint(1, 20) for _ in range(n)]
            m = rng.randint(1, n)
            if pid == 'P1886':
                values = [rng.randint(-20, 20) for _ in range(n)]
            if pid == 'B3666':
                values = [rng.randrange(1, 2 ** 64) for _ in range(n)]
            if pid == 'UVA1619':
                values = [rng.randint(0, 10) for _ in range(n)]
            line = ' '.join(map(str, values)) + '\n'
            if pid == 'P1440':
                put(f'{n} {m}\n' + line, '\n'.join((str(min(values[max(0, i - m):i])) if i else '0' for i in range(n))))
            elif pid in ['P1886', 'P2251']:
                low = [min(values[i:i + m]) for i in range(n - m + 1)]
                expected = '\n'.join(map(str, low)) if pid == 'P2251' else ' '.join(map(str, low)) + '\n' + ' '.join((str(max(values[i:i + m])) for i in range(n - m + 1)))
                put(f'{n} {m}\n' + line, expected)
            elif pid in ['P2947', 'P5788']:
                separator='\n' if pid=='P2947' else ' '
                put(str(n) + '\n' + line, separator.join((str(next((j + 1 for j in range(i + 1, n) if values[j] > values[i]), 0)) for i in range(n))))
            elif pid == 'B3666':
                answers = []
                for right in range(n):
                    value = 0
                    for i in range(right + 1):
                        if all((values[i] > values[j] for j in range(i + 1, right + 1))):
                            value ^= i + 1
                    answers.append(value)
                put(str(n) + '\n' + line, '\n'.join(map(str, answers)))
            elif pid == 'UVA1619':
                best = max(((min(values[l:r + 1]) * sum(values[l:r + 1]), -(r - l + 1), -l, r) for l in range(n) for r in range(l, n)))
                put(str(n) + '\n' + line, f'{best[0]}\n{-best[2] + 1} {best[3] + 1}')
            elif pid == 'P6503':
                put(str(n) + '\n' + line, sum((max(values[l:r + 1]) - min(values[l:r + 1]) for l in range(n) for r in range(l, n))))
            elif pid == 'CF547B':
                put(str(n) + '\n' + line, ' '.join((str(max((min(values[i:i + size]) for i in range(n - size + 1)))) for size in range(1, n + 1))))
            else:
                answers = []
                for start in range(n):
                    largest = values[start]
                    answer = -1
                    for length in range(1, 3 * n + 1):
                        x = values[(start + length) % n]
                        if 2 * x < largest:
                            answer = length
                            break
                        largest = max(largest, x)
                    answers.append(answer)
                put(str(n) + '\n' + line, ' '.join(map(str, answers)))
        elif pid == 'P1628':
            words = [''.join((rng.choice('abc') for _ in range(rng.randint(1, 8)))) for _ in range(rng.randint(1, 20))]
            prefix = ''.join((rng.choice('abc') for _ in range(rng.randint(1, 5))))
            put(str(len(words)) + '\n' + '\n'.join(words) + '\n' + prefix + '\n', '\n'.join(sorted((x for x in words if x.startswith(prefix)))))
        elif pid == 'UVA11462':
            values = [rng.randint(1, 99) for _ in range(rng.randint(1, 100))]
            put(str(len(values)) + '\n' + ' '.join(map(str, values)) + '\n0\n', ' '.join(map(str, sorted(values))))
        elif pid == 'P15232':
            n = rng.randint(1, 4)
            m = rng.randint(1, 7)
            cost = [rng.randint(1, 20) for _ in range(n)]
            b = [rng.randint(1, m + 1) for _ in range(m)]
            put(f'{n} {m}\n' + ' '.join(map(str, cost)) + '\n' + ' '.join(map(str, b)) + '\n', road(cost, b))
        elif pid == 'P2564':
            k = rng.randint(1, 5)
            groups = [sorted((rng.randint(0, 20) for _ in range(rng.randint(1, 5)))) for _ in range(k)]
            n = sum(map(len, groups))
            best = min((max(choice) - min(choice) for choice in product(*groups)))
            put(f'{n} {k}\n' + ''.join((str(len(g)) + ' ' + ' '.join(map(str, g)) + '\n' for g in groups)), best)
        elif pid in ['P1950', 'P7410']:
            h = rng.randint(1, 5)
            w = h if pid == 'P7410' else rng.randint(1, 5)
            if pid == 'P1950':
                matrix = [[rng.choice('.*') for _ in range(w)] for _ in range(h)]
                put(f'{h} {w}\n' + '\n'.join((''.join(row) for row in matrix)) + '\n', rectangle_count(matrix, lambda cells: all((x == '.' for x in cells))))
            else:
                matrix = [[rng.choice([1, 99, 100, 101, 200]) for _ in range(w)] for _ in range(h)]
                put(str(h) + '\n' + '\n'.join((' '.join(map(str, row)) for row in matrix)) + '\n', rectangle_count(matrix, lambda cells: min(cells) == 100))
        elif pid == 'P9977':
            n = rng.randint(1, 4)
            weights = rng.sample(range(1, 15), n)
            counts = [rng.randint(1, 2) for _ in range(n)]
            m = rng.randint(1, 3)
            k = rng.randint(1, 7)
            expanded = [w for w, c in zip(weights, counts) for _ in range(c)]
            put(f'{n} {m} {k}\n' + ''.join((f'{w} {c}\n' for w, c in zip(weights, counts))), towers(expanded, m, k))
        elif pid == 'P10277':
            n = rng.randint(1, 10)
            k = rng.randint(1, min(n, 4))
            durations = [rng.randint(1, 10) for _ in range(n)]
            put(f'{n} {k}\n' + ' '.join(map(str, durations)) + '\n', interviews(durations, k))
    if pid=='P1628':
        n=100000;word='a'*100;put(str(n)+'\n'+(word+'\n')*n+'a\n',(word+'\n')*n)
        put('2\na\naa\n'+'a'*101+'\n','')
    elif pid=='UVA11462':
        n=2000000;put(str(n)+'\n'+('99 '*(n-1))+'99\n0\n',('99 '*(n-1))+'99')
        put('1\n1\n1\n99\n0\n','1\n99')
    elif pid=='B3666':
        put('1\n18446744073709551615\n',1)
        n=1000000;put(str(n)+'\n'+row(range(2**64-n,2**64)),'\n'.join(map(str,range(1,n+1))))
        def xor_prefix(x):return [x,1,x+1,0][x%4]
        put(str(n)+'\n'+row(range(n,0,-1)),'\n'.join(str(xor_prefix(i)) for i in range(1,n+1)))
        put('4\n9 9 9 9\n','1\n2\n3\n4')
    elif pid=='P1440':
        put('1 1\n7\n',0)
        n=2000000;put(f'{n} {n}\n'+row(range(1,n+1)),'0\n'+'1\n'*(n-1))
        put('4 1\n7 3 8 2\n','0\n7\n3\n8')
    elif pid=='P1886':
        put('1 1\n2147483647\n','2147483647\n2147483647')
        n=1000000;low=-2**31;put(f'{n} {n}\n'+row(range(low,low+n)),str(low)+'\n'+str(low+n-1))
    elif pid=='P2251':
        put('1 1\n7\n',7)
        n=100000;put(f'{n} {n}\n'+row(range(1,n+1)),1)
    elif pid=='P2947':
        put('1\n7\n',0)
        n=100000;put(str(n)+'\n'+row(range(1,n+1)),'\n'.join(map(str,range(2,n+1)))+'\n0')
        put(str(n)+'\n'+row(range(n,0,-1)),'0\n'*n)
    elif pid=='P5788':
        put('1\n7\n',0)
        n=3000000;put(str(n)+'\n'+row(range(1,n+1)),row(range(2,n+1))[:-1]+' 0')
    elif pid=='P15232':
        m=100000;put(f'1 {m}\n1000000000\n'+row([1000000000]*m),10**14)
        put(f'1 {m}\n1\n'+row([1]*m),-1)
        put('3 7\n1 2 9\n2 2 2 2 4 4 4\n',25)
    elif pid=='UVA1619':
        n=100000;put(str(n)+'\n'+row([1000000]*n),f'{10**17}\n1 {n}')
        put(str(n)+'\n'+row([0]*n),'0\n1 1')
        put('1\n0\n\n3\n1 1 1\n\n5\n2 0 2 0 2\n','0\n1 1\n\n3\n1 3\n\n4\n1 1')
    elif pid=='P1950':
        n=m=1000;put(f'{n} {m}\n'+('.'*m+'\n')*n,(n*(n+1)//2)*(m*(m+1)//2))
        put(f'{n} {m}\n'+('*'*m+'\n')*n,0)
        grid=[''.join('.' if (i+j)%2==0 else '*' for j in range(m)) for i in range(n)];put(f'{n} {m}\n'+'\n'.join(grid)+'\n',n*m//2)
    elif pid=='P2564':
        n=1000000;part=n//2;put(f'{n} 2\n'+str(part)+' '+row([0]*part)+str(n-part)+' '+row([2147483647]*(n-part)),2147483647)
        put('60 60\n'+'1 0\n'*60,0)
    elif pid=='P6503':
        n=300000;put(str(n)+'\n'+row([100000000]*n),0)
        values=[1 if i%2==0 else 100000000 for i in range(n)];put(str(n)+'\n'+row(values),(n*(n+1)//2-n)*99999999)
    elif pid=='P7410':
        n=500
        for value in [99,100,101]:put(str(n)+'\n'+(row([value]*n))*n,(n*(n+1)//2)**2 if value==100 else 0)
        at=n//2;matrix=[[101]*n for _ in range(n)];matrix[at][at]=100;put(str(n)+'\n'+''.join(row(r) for r in matrix),((at+1)*(n-at))**2)
        for value in [99,100,101]:put('1\n'+str(value)+'\n',int(value==100))
    elif pid=='P9977':
        n=200000;put(f'{n} 1000000000 1\n'+''.join(f'{i} 1000000000\n' for i in range(1,n+1)),n*1000000000)
        put('2 1000000000 1000000000\n1 1000000000\n1000000000 1000000000\n',1000000000)
    elif pid=='P10277':
        n=300000;put(f'{n} 1\n'+row([1000000000]*n),str(n*1000000000)+'\n1')
        put(f'{n} {n}\n'+row([1000000000]*n),'1000000000\n'+'1'*n)
        put('12 3\n2 10 10 11 10 4 1 10 8 5 8 5\n','25\n011')
    elif pid=='CF547B':
        n=200000;put(str(n)+'\n'+row(range(1,n+1)),row(range(n,0,-1)))
        put(str(n)+'\n'+row([1000000000]*n),row([1000000000]*n))
    elif pid=='CF1237D':
        n=100000;put(str(n)+'\n'+row([1000000000]*n),row([-1]*n))
        put(str(n)+'\n'+row([1000000000]+[1]*(n-1)),row([1]+list(range(n,1,-1))))
        put('2\n6 3\n','-1 -1');put('2\n7 3\n','1 2')

    return result
