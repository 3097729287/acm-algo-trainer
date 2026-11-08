## P3385 负环

原题：[P3385](https://www.luogu.com.cn/problem/P3385)

### 从问题到算法

从一号点出发的最短简单路径至多包含 n−1 条边。如果不存在可达负环，所有有效最短路都可去掉非负回路，因此 n−1 轮松弛已足够。第 n 轮仍能改进的路径必然借助某个可达负环。

初始化只有顶点一可达，松弛前跳过不可达起点，这样不会把其它连通区域的负环误报。非负输入边要添加两个方向，负边只添加输入方向；m 是输入记录数，不是最终边数。

每轮按边顺序原地松弛可能传播多条边，但不会使无负环图在第 n 轮产生更新。没有更新时可以提前结束。

### 复杂度

时间 O(Tnm)，空间 O(n+m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        int n, m;
        cin >> n >> m;
        vector<tuple<int, int, int>> e;
        while (m--) {
            int u, v, w;
            cin >> u >> v >> w;
            u--;
            v--;
            e.push_back({u, v, w});
            if (w >= 0)
                e.push_back({v, u, w});
        }
        const long long INF = 1LL << 60;
        vector<long long> d(n, INF);
        d[0] = 0;
        bool negative = false;
        for (int round = 1; round <= n; round++) {
            bool changed = false;
            for (auto [u, v, w] : e)
                if (d[u] != INF && d[v] > d[u] + w) {
                    d[v] = d[u] + w;
                    changed = true;
                }
            if (!changed)
                break;
            if (round == n)
                negative = true;
        }
        cout << (negative ? "YES" : "NO") << '\n';
    }

    return 0;
}
```

### 实现提醒

仅判断一号点可达的负环；负边不自动反向；距离用 long long。
