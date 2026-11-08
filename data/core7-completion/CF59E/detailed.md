## CF59E Shortest Path

原题：[CF59E](https://www.luogu.com.cn/problem/CF59E)

### 从问题到算法

仅记录当前点会把不同来路混在一起：同一顶点从不同前驱进入，允许的下一步可能不同。状态 (prev,cur) 足以检查禁止三元组 (prev,cur,next)。起点使用一个虚拟前驱，第一次走边不受三元组约束。

每次转移走一条边，普通 BFS 给出最短边数。前驱数组同时作为访问标记，记录从哪个状态到达，以便逆序恢复顶点。终点可以由任意前驱进入，第一次出队的终点状态就是最短答案。

禁止三元组按三进制位置式编码成六十四位整数后存哈希集合；状态用整数编码，避免为每条候选路线复制完整路径。

### 复杂度

时间 O(n²+Σdeg(v)²+k)，空间 O(n²+m+k)；实际只扩展可达的有向边状态。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, k;
    cin >> n >> m >> k;
    vector<vector<int>> g(n);
    while (m--) {
        int a, b;
        cin >> a >> b;
        a--;
        b--;
        g[a].push_back(b);
        g[b].push_back(a);
    }
    unordered_set<long long> bad;
    auto key = [&](int a, int b, int c) { return (1LL * a * n + b) * n + c; };
    while (k--) {
        int a, b, c;
        cin >> a >> b >> c;
        bad.insert(key(a - 1, b - 1, c - 1));
    }
    vector<int> parent((n + 1) * n, -2), q = {n * n};
    parent[n * n] = -1;
    int goal = -1;
    for (int i = 0; i < (int)q.size(); i++) {
        int state = q[i], pre = state / n, v = state % n;
        if (v == n - 1) {
            goal = state;
            break;
        }
        for (int u : g[v])
            if (!bad.count(key(pre, v, u))) {
                int next = v * n + u;
                if (parent[next] == -2) {
                    parent[next] = state;
                    q.push_back(next);
                }
            }
    }
    if (goal < 0) {
        cout << -1 << '\n';
        return 0;
    }
    vector<int> path;
    for (int s = goal; s >= 0; s = parent[s])
        path.push_back(s % n + 1);
    reverse(path.begin(), path.end());
    cout << path.size() - 1 << '\n';
    for (int i = 0; i < (int)path.size(); i++)
        cout << path[i] << (i + 1 == (int)path.size() ? '\n' : ' ');

    return 0;
}
```

### 实现提醒

状态不能只记当前点；禁止关系有方向；无解输出 −1。
