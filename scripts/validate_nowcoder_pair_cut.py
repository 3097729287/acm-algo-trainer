"""Exhaust all shortest paths on small graphs, plus two maximum-size shapes."""
import json
import random
import subprocess
import time

from nowcoder_editorials import CONTENT, OUT, ROOT, program, read, sha, write


def main():
    rng = random.Random(2026110809)
    entry = read(CONTENT / 'reviewed.json')['nowcoder-global::14501']
    code = program((ROOT / entry['articles']['default']).read_text(encoding='utf-8'))
    folder = OUT / 'compiled/14501'
    assert code.strip() in (folder / 'main.cpp').read_text(encoding='utf-8')
    timings = []
    def check(n, edges, s, t, expected):
        data = f'{n} {len(edges)} {s + 1} {t + 1}\n' + ''.join(f'{a + 1} {b + 1} {w}\n' for a,b,w in edges)
        start = time.perf_counter()
        result = subprocess.run([str(folder / 'main.exe')], input=data, text=True, capture_output=True, timeout=12)
        elapsed = time.perf_counter() - start
        assert result.returncode == 0 and result.stdout.strip() == str(expected), (data, expected, result.stdout, result.stderr)
        return elapsed
    for test in range(500):
        n = rng.randint(2, 10)
        s,t = rng.randrange(n),rng.randrange(n)
        if test % 2:
            heights = sorted(rng.sample(range(1,40),n))
            edges = [(a,b,heights[b] - heights[a]) for a in range(n) for b in range(a + 1,n) if rng.random() < 0.4]
            s,t = 0,n-1
        else:
            edges = [(a,b,rng.randint(1,7)) for a in range(n) for b in range(a + 1,n) if rng.random() < 0.35]
        inf = 10**9
        distance = [[inf] * n for _ in range(n)]
        adjacency = [[] for _ in range(n)]
        for i in range(n): distance[i][i] = 0
        for a,b,w in edges:
            distance[a][b] = distance[b][a] = w
            adjacency[a].append((b,w));adjacency[b].append((a,w))
        for k in range(n):
            for i in range(n):
                for j in range(n): distance[i][j] = min(distance[i][j],distance[i][k] + distance[k][j])
        paths = []
        def enumerate_paths(u, mask):
            if u == t:
                paths.append(mask);return
            for v,w in adjacency[u]:
                if distance[s][u] + w + distance[v][t] == distance[s][t]:
                    enumerate_paths(v,mask | (1 << v))
        if distance[s][t] < inf: enumerate_paths(s,1 << s)
        expected = sum(all(((mask >> a & 1) + (mask >> b & 1)) == 1 for mask in paths)
                       for a in range(n) for b in range(a + 1,n))
        check(n,edges,s,t,expected)
    n = 50000
    chain = [(i,i + 1,1) for i in range(n - 1)]
    timings.append({'shape':'chain','vertices':n,'edges':len(chain),'expected':0,'seconds':check(n,chain,0,n-1,0)})
    paths = [[0] + list(range(1,25000)) + [n-1], [0] + list(range(25000,n-1)) + [n-1]]
    parallel = [(a,b,1) for path in paths for a,b in zip(path,path[1:])]
    answer = 24999**2
    timings.append({'shape':'parallel-paths','vertices':n,'edges':len(parallel),'expected':answer,
                    'seconds':check(n,parallel,0,n-1,answer)})
    report = {'passed':True,'randomSeed':2026110809,'exhaustiveFixtures':500,'maximumShapes':timings,
              'programSha256':sha(code),'executableSha256':sha((folder/'main.exe').read_bytes())}
    write(OUT / 'pair-cut-independent-validation.json',report)
    print(json.dumps(report))


if __name__ == '__main__': main()
