## CF796D Police Stations

原题：[CF796D](https://www.luogu.com.cn/problem/CF796D)

### 思路

将所有不同的警局城市同时入队，为每个城市分配最近警局。两个不同归属区域之间的树边全部关闭，区域内部保留搜索树边。

### 复杂度

时间 O(n+k)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k, d;
    cin >> n >> k >> d;
    vector<int> owner(n, -1), q;
    for (int i = 0; i < k; i++) {
        int p;
        cin >> p;
        p--;
        if (owner[p] < 0) {
            owner[p] = p;
            q.push_back(p);
        }
    }
    vector<vector<pair<int, int>>> g(n);
    vector<pair<int, int>> e;
    for (int i = 1; i < n; i++) {
        int a, b;
        cin >> a >> b;
        a--;
        b--;
        e.push_back({a, b});
        g[a].push_back({b, i});
        g[b].push_back({a, i});
    }
    for (int i = 0; i < (int)q.size(); i++) {
        int v = q[i];
        for (auto [u, id] : g[v])
            if (owner[u] < 0) {
                owner[u] = owner[v];
                q.push_back(u);
            }
    }
    vector<int> cut;
    for (int i = 0; i < n - 1; i++)
        if (owner[e[i].first] != owner[e[i].second])
            cut.push_back(i + 1);
    cout << cut.size() << '\n';
    for (int i = 0; i < (int)cut.size(); i++)
        cout << cut[i] << (i + 1 == (int)cut.size() ? '\n' : ' ');
    if (cut.empty())
        cout << '\n';

    return 0;
}
```

### 实现提醒

同城多个警局只算一个源；保留首次访问的归属；输出原边编号。
