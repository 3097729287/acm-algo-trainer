"""Exhaustive partitions, literal game steps and small graph definitions."""
from itertools import combinations, combinations_with_replacement, product
import json
import random
import subprocess
import time

from nowcoder_editorials import CONTENT, OUT, ROOT, program, read, sha, write

RNG = random.Random(2026110810)
LEDGER = read(CONTENT / 'reviewed.json')
COUNTS = {}
PERFORMANCE = []


def check(number, data, expected, timed=False):
    entry = LEDGER[f'nowcoder-global::{number}']
    code = program((ROOT / entry['articles']['default']).read_text(encoding='utf-8'))
    folder = OUT / 'compiled' / str(number)
    assert code.strip() in (folder / 'main.cpp').read_text(encoding='utf-8')
    start = time.perf_counter()
    run = subprocess.run([str(folder / 'main.exe')], input=data, text=True, capture_output=True, timeout=12)
    elapsed = time.perf_counter() - start
    expected = ' '.join(map(str, expected)) if isinstance(expected, list) else str(expected)
    assert run.returncode == 0 and run.stdout.split() == expected.split(), (number, data[:6000], expected, run.stdout, run.stderr)
    COUNTS[str(number)] = COUNTS.get(str(number), 0) + 1
    if timed: PERFORMANCE.append({'problem':number,'seconds':elapsed,'expected':expected})


def partitions_and_hulls():
    for _ in range(40):
        n = RNG.randint(1, 10)
        a = [RNG.randint(1, 12) for _ in range(n)]
        target = RNG.randint(1, 18)
        toy = 10**30
        days = RNG.randint(1, n)
        variance = 10**30
        segment_limit = RNG.randint(0, 25)
        sequence = -1
        b = [RNG.randint(0, 9) for _ in range(n)]
        for mask in range(1 << (n - 1)):
            parts, current = [], []
            for i in range(n):
                current.append(i)
                if i == n - 1 or mask >> i & 1:
                    parts.append(current); current = []
            toy = min(toy, sum((sum(a[i] for i in p) + len(p) - 1 - target)**2 for p in parts))
            if len(parts) == days:
                sums = [sum(b[i] for i in p) for p in parts]
                variance = min(variance, days * sum(s*s for s in sums) - sum(b)**2)
            if all(sum(b[i] for i in p) <= segment_limit for p in parts):
                value = sum(max(b[i] for i in p) for p in parts)
                sequence = value if sequence == -1 else min(sequence, value)
        check(20067, f'{n} {target}\n' + '\n'.join(map(str, a)), toy)
        check(20384, f'{n} {days}\n' + ' '.join(map(str, b)), variance)
        check(51196, f'{n} {segment_limit}\n' + ' '.join(map(str, b)), sequence)
        n = RNG.randint(1, 8)
        position, quantity, cost = [], [], []
        x = 0
        for i in range(n):
            x += RNG.randint(1, 5) if i else 0
            position.append(x); quantity.append(RNG.randint(0, 5)); cost.append(RNG.randint(0, 15))
        best = 10**30
        for mask in range(1 << n):
            score = sum(cost[i] for i in range(n) if mask >> i & 1)
            for i in range(n):
                if not quantity[i]: continue
                next_warehouse = next((j for j in range(i, n) if mask >> j & 1), None)
                if next_warehouse is None: break
                score += quantity[i] * (position[next_warehouse] - position[i])
            else: best = min(best, score)
        check(20601, str(n) + '\n' + ''.join(f'{x} {p} {c}\n' for x,p,c in zip(position,quantity,cost)), best)
    n = 50000
    check(20067, f'{n} 1\n' + '10000000\n' * n, n * (10000000 - 1)**2, True)
    check(20384, '3000 3000\n' + '10 ' * 3000, 0, True)
    n = 1000000
    check(20601, str(n) + '\n' + ''.join(f'{i} 1 0\n' for i in range(n)), 0, True)


def literal_motion_and_cut():
    for _ in range(35):
        rows, cols = RNG.randint(1, 4), RNG.randint(1, 4)
        grid = [['x' if RNG.random() < 0.2 else '.' for _ in range(cols)] for _ in range(rows)]
        start = RNG.randrange(rows), RNG.randrange(cols)
        grid[start[0]][start[1]] = '.'
        intervals = [(RNG.randint(1, 4), RNG.randint(1, 4)) for _ in range(RNG.randint(1, 5))]
        states = {start:0}
        directions = {1:(-1,0),2:(1,0),3:(0,-1),4:(0,1)}
        for duration, direction in intervals:
            dr,dc = directions[direction]
            for second in range(duration):
                next_states = dict(states)
                for (r,c), score in states.items():
                    rr,cc = r+dr,c+dc
                    if 0 <= rr < rows and 0 <= cc < cols and grid[rr][cc] != 'x':
                        next_states[rr,cc] = max(next_states.get((rr,cc),-1),score+1)
                states = next_states
        data = f'{rows} {cols} {start[0]+1} {start[1]+1} {len(intervals)}\n' + '\n'.join(''.join(r) for r in grid) + '\n'
        current = 1
        for duration,direction in intervals:
            data += f'{current} {current+duration-1} {direction}\n';current += duration
        check(17395,data,max(states.values()))
        rows,cols = RNG.randint(1,3),RNG.randint(1,4)
        animals = [RNG.randrange(3) for _ in range(rows*cols)]
        free = [i for i,a in enumerate(animals) if a == 0]
        best = 10**9
        for values in product((1,2),repeat=len(free)):
            state = animals[:]
            for p,v in zip(free,values): state[p] = v
            score = sum(state[r*cols+c] != state[rr*cols+cc]
                        for r in range(rows) for c in range(cols)
                        for rr,cc in [(r+1,c),(r,c+1)] if rr < rows and cc < cols)
            best = min(best,score)
        check(20488,f'{rows} {cols}\n' + ' '.join(map(str,animals)),best)
        m,n = RNG.randint(1,150),RNG.randint(1,10)
        steps = [RNG.randint(1,300) for _ in range(n)]
        occupied = {0}
        for a in steps:
            current = a % m
            while current:
                occupied.add(current);current = (current+a)%m
        check(124160,f'1\n{n} {m}\n' + ' '.join(map(str,steps)),f'Case #1: {sum(occupied)}')


def minimum_unique_mst_and_ski():
    for _ in range(35):
        n = RNG.randint(1,6)
        all_edges = list(combinations(range(n),2))
        edges = [(RNG.randrange(v),v,RNG.randint(1,5)) for v in range(1,n)]
        used = {(a,b) for a,b,w in edges}
        RNG.shuffle(all_edges)
        for a,b in all_edges:
            if (a,b) not in used and RNG.random() < 0.4 and len(edges) < 9:
                edges.append((a,b,RNG.randint(1,5)));used.add((a,b))
        def reachable(selected,directed=False,heights=None):
            adjacency = [[] for _ in range(n)]
            for j in selected:
                a,b,w = edges[j]
                if not directed or heights[a] >= heights[b]: adjacency[a].append(b)
                if not directed or heights[b] >= heights[a]: adjacency[b].append(a)
            seen = {0};queue = [0]
            for u in queue:
                for v in adjacency[u]:
                    if v not in seen: seen.add(v);queue.append(v)
            return seen
        trees = []
        for chosen in combinations(range(len(edges)),n-1):
            if len(reachable(chosen)) == n:
                trees.append((sum(edges[j][2] for j in chosen),sum(1<<j for j in chosen)))
        minimum = min(cost for cost,mask in trees)
        mst = [mask for cost,mask in trees if cost == minimum]
        deletion = min(sum(w for j,(_,_,w) in enumerate(edges) if removed >> j & 1)
                       for removed in range(1<<len(edges)) if sum(not(mask & removed) for mask in mst) == 1)
        check(53074,f'{n} {len(edges)}\n'+''.join(f'{a+1} {b+1} {w}\n' for a,b,w in edges),deletion)
        heights = [RNG.randint(1,4) for _ in range(n)]
        wanted = reachable(range(len(edges)),True,heights)
        best = min(sum(edges[j][2] for j in chosen)
                   for chosen in combinations(range(len(edges)),len(wanted)-1)
                   if reachable(chosen,True,heights) == wanted)
        check(20568,f'{n} {len(edges)}\n'+' '.join(map(str,heights))+'\n'+''.join(f'{a+1} {b+1} {w}\n' for a,b,w in edges),[len(wanted),best])


def constraints():
    for _ in range(30):
        n = RNG.randint(1,5)
        rules = [(RNG.randint(1,5),RNG.randrange(n),RNG.randrange(n)) for _ in range(RNG.randint(0,7))]
        def valid(values):
            for t,a,b in rules:
                x,y = values[a],values[b]
                if not {1:x==y,2:x<y,3:x>=y,4:x>y,5:x<=y}[t]: return False
            return True
        best = min((sum(values) for values in product(range(1,n+1),repeat=n) if valid(values)),default=-1)
        check(20284,f'{n} {len(rules)}\n'+''.join(f'{t} {a+1} {b+1}\n' for t,a,b in rules),best)
        n = RNG.randint(2,4)
        pairs = list(combinations(range(n),2))
        close = [(a,b,RNG.randint(1,4)) for a,b in pairs if RNG.random() < 0.5]
        far = [(a,b,RNG.randint(1,4)) for a,b in pairs if RNG.random() < 0.35]
        answers = []
        for tail in combinations_with_replacement(range(16),n-1):
            values = (0,) + tail
            if all(values[b]-values[a] <= w for a,b,w in close) and all(values[b]-values[a] >= w for a,b,w in far):
                answers.append(values[-1])
        best = -1 if not answers else -2 if max(answers) == 15 else max(answers)
        check(50390,f'{n} {len(close)} {len(far)}\n'+''.join(f'{a+1} {b+1} {w}\n' for a,b,w in close+far),best)


def all_shortest_road_paths():
    for _ in range(30):
        n = RNG.randint(2,7)
        edges = [(a,b,RNG.randint(1,5)) for a in range(n) for b in range(n) if a!=b and RNG.random()<0.25]
        if not edges: edges = [(0,1,1)]
        inf = 10**9
        distance = [[0 if a==b else inf for b in range(n)] for a in range(n)]
        adjacency = [[] for _ in range(n)]
        for j,(a,b,w) in enumerate(edges): distance[a][b] = min(distance[a][b],w);adjacency[a].append(j)
        for k in range(n):
            for a in range(n):
                for b in range(n): distance[a][b] = min(distance[a][b],distance[a][k]+distance[k][b])
        answer = [0]*len(edges)
        for source in range(n):
            for target in range(n):
                if distance[source][target] == inf: continue
                def dfs(u,path):
                    if u==target:
                        for edge in path: answer[edge]+=1
                        return
                    for edge in adjacency[u]:
                        a,v,w = edges[edge]
                        if distance[source][u]+w+distance[v][target] == distance[source][target]: dfs(v,path+[edge])
                dfs(source,[])
        check(19987,f'{n} {len(edges)}\n'+''.join(f'{a+1} {b+1} {w}\n' for a,b,w in edges),answer)


if __name__ == '__main__':
    partitions_and_hulls()
    literal_motion_and_cut()
    minimum_unique_mst_and_ski()
    constraints()
    all_shortest_road_paths()
    report = {'passed':True,'randomSeed':2026110810,'fixtures':sum(COUNTS.values()),'performance':PERFORMANCE,
              'problems':{number:{'fixtures':count,'programSha256':LEDGER['nowcoder-global::'+number]['programSha256']}
                          for number,count in COUNTS.items()}}
    write(OUT/'optimized-independent-validation.json',report)
    print(json.dumps(report))
