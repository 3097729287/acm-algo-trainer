## P3645 雅加达的摩天楼

原题：[P3645](https://www.luogu.com.cn/problem/P3645)

### 从问题到算法

若为每条狗都沿整条同余链扩展，最坏会重复平方次。取阈值 B≈sqrt(n)，按跳长分情况。

p<B 时，把 (p,楼号) 作为共享状态：从持有该狗的楼可零代价进入，状态内向左右 p 格移动代价一，也可零代价回到普通楼状态换狗。所有同跳长的狗共享这一层。

p≥B 时，一次持狗能到达的楼不超过 O(n/B)，从普通楼直接连到这些楼，代价是距离除以 p。无需保存大跳层。

所有边权非负，Dijkstra 按最小跳数扩展。普通楼状态只在最短距离确定时处理狗，大跳展开总计 O(mn/B)，小跳状态 O(nB)。起点和终点是输入前两只狗所在楼，楼号原本从零开始。

### 复杂度

时间 O((nB+mn/B) log(nB))，空间 O(nB+m)，B≈sqrt(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    int B = max(2, (int)sqrt(n) + 1), start = 0, goal = 0;
    vector<vector<int>> dogs(n);
    for (int i = 0; i < m; i++) {
        int b, p;
        cin >> b >> p;
        dogs[b].push_back(p);
        if (i == 0)
            start = b;
        if (i == 1)
            goal = b;
    }
    for (auto &v : dogs) {
        sort(v.begin(), v.end());
        v.erase(unique(v.begin(), v.end()), v.end());
    }
    const int INF = 1000000000;
    vector<int> d(n * B, INF);
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>> heap;
    d[start] = 0;
    heap.push({0, start});
    auto relax = [&](int state, int value) {
        if (value < d[state]) {
            d[state] = value;
            heap.push({value, state});
        }
    };
    while (!heap.empty()) {
        auto [dist, state] = heap.top();
        heap.pop();
        if (d[state] != dist)
            continue;
        int p = state / n, v = state % n;
        if (!p) {
            if (v == goal) {
                cout << dist << '\n';
                return 0;
            }
            for (int jump : dogs[v]) {
                if (jump < B)
                    relax(jump * n + v, dist);
                else {
                    int cost = 1;
                    for (int u = v + jump; u < n; u += jump, cost++)
                        relax(u, dist + cost);
                    cost = 1;
                    for (int u = v - jump; u >= 0; u -= jump, cost++)
                        relax(u, dist + cost);
                }
            }
        } else {
            relax(v, dist);
            if (v + p < n)
                relax(p * n + v + p, dist + 1);
            if (v - p >= 0)
                relax(p * n + v - p, dist + 1);
        }
    }
    cout << -1 << '\n';

    return 0;
}
```

### 实现提醒

进入小跳层不花步数；普通状态才能换狗；起终来自前两条记录。
