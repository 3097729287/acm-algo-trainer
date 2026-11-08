## CF59E Shortest Path

原题：[CF59E](https://www.luogu.com.cn/problem/CF59E)

### 思路

下一步是否合法取决于上一个点和当前点，因此用 (prev,cur) 作为状态。沿未被禁止的三元组转移并保存前驱，第一次到终点时还原最短路线。

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
