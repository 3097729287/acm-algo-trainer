## P4408 逃学的小孩 / 数据生成器

原题：[P4408](https://www.luogu.com.cn/problem/P4408)

### 从问题到算法

给定三处位置 A、B、C，先去较近朋友家再去另一家，最坏耗时为 dist(A,B)+min(dist(C,A),dist(C,B))。要让这个值最大，可以将朋友家取为一组树直径端点。

使用树的直径替换引理：对任意三点形成的三叉子树，若两处朋友不是直径端点，将分支延伸或替换到直径两端，不会减小“朋友间距离加家到较近朋友距离”的最大值。也可以把三点投影到直径路径证明：直径外任意分支高度不超过其投影到直径两端距离的较小者，否则会产生更长直径；把这个上界代入三叉子树的三段长度即可得到公式的上界。取朋友为直径两端又能达到公式，因此上下界相等。

从任一点找最远点 A，再从 A 找最远点 B，得到直径。树上只有一条路，遍历累加边权即可求距离，不需要 Dijkstra。再从 B 遍历一次，枚举 C 即可。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<vector<pair<int, long long>>> g(n);
    while (m--) {
        int a, b;
        long long w;
        cin >> a >> b >> w;
        a--;
        b--;
        g[a].push_back({b, w});
        g[b].push_back({a, w});
    }
    auto distances = [&](int s) {
        vector<long long> d(n, -1);
        vector<int> q = {s};
        d[s] = 0;
        for (int i = 0; i < (int)q.size(); i++)
            for (auto [u, w] : g[q[i]])
                if (d[u] < 0) {
                    d[u] = d[q[i]] + w;
                    q.push_back(u);
                }
        return d;
    };
    auto d = distances(0);
    int A = max_element(d.begin(), d.end()) - d.begin();
    auto x = distances(A);
    int B = max_element(x.begin(), x.end()) - x.begin();
    auto y = distances(B);
    long long extra = 0;
    for (int i = 0; i < n; i++)
        extra = max(extra, min(x[i], y[i]));
    cout << x[B] + extra << '\n';

    return 0;
}
```

### 实现提醒

边权可为零；答案和路径长度用 long long；按较近的朋友先找。
