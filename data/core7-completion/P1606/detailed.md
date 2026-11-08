## P1606 Lilypad Pond G

原题：[P1606](https://www.luogu.com.cn/problem/P1606)

### 从问题到算法

不能直接对原网格最短跳跃计数：已有荷叶间可以绕行，同一组新增荷叶会对应许多跳跃路线。应消去这些不花代价的内部路线。

新图只保留所有水面、起点和终点。对每个源结点，沿马步遍历可直接或经已有荷叶到达的位置；遇到其它水面或终点就记录为下一站，不继续穿过该水面。同一目标只连一条边，所以经过已有荷叶的不同走法被合并。

新图的一条起终路径每经过一个内部结点就新增一片荷叶，因此新增数是路径边数减一。用 BFS 求最短边数，并在相同最短距离时累加条数。最小摆放方案不含多余水面；若同一最小水面集合能以两种不同次序连接起终点，就能从分歧处绕去至少一个水面，与最小性矛盾。因此这种压缩后的最短路径与最小摆放方案一一对应。

### 复杂度

设格子数 V=MN，时间 O(V²)，空间 O(V²)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    int N = n * m, start = -1, goal = -1;
    vector<int> a(N), id(N, -1), cells;
    for (int i = 0; i < N; i++) {
        cin >> a[i];
        if (a[i] == 3)
            start = i;
        if (a[i] == 4)
            goal = i;
        if (a[i] == 0 || a[i] >= 3) {
            id[i] = cells.size();
            cells.push_back(i);
        }
    }
    int z = cells.size();
    vector<vector<int>> g(z);
    int dx[8] = {1, 1, -1, -1, 2, 2, -2, -2}, dy[8] = {2, -2, 2, -2, 1, -1, 1, -1};
    for (int k = 0; k < z; k++) {
        vector<char> seen(N);
        vector<int> q = {cells[k]};
        seen[cells[k]] = 1;
        for (int h = 0; h < (int)q.size(); h++) {
            int v = q[h], x = v / m, y = v % m;
            for (int d = 0; d < 8; d++) {
                int nx = x + dx[d], ny = y + dy[d];
                if (nx < 0 || nx >= n || ny < 0 || ny >= m)
                    continue;
                int u = nx * m + ny;
                if (a[u] == 2 || seen[u])
                    continue;
                seen[u] = 1;
                if (id[u] >= 0)
                    g[k].push_back(id[u]);
                else
                    q.push_back(u);
            }
        }
    }
    int s = id[start], t = id[goal];
    vector<int> d(z, -1), q = {s};
    vector<long long> ways(z);
    d[s] = 0;
    ways[s] = 1;
    for (int i = 0; i < (int)q.size(); i++) {
        int v = q[i];
        for (int u : g[v]) {
            if (d[u] < 0) {
                d[u] = d[v] + 1;
                q.push_back(u);
            }
            if (d[u] == d[v] + 1)
                ways[u] += ways[v];
        }
    }
    if (d[t] < 0)
        cout << -1 << '\n';
    else
        cout << d[t] - 1 << '\n' << ways[t] << '\n';

    return 0;
}
```

### 实现提醒

同一源目标只能连一次；已有荷叶不是新增荷叶；无解只输出 −1。
