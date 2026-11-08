## P7480 Reboot from Blue

原题：[P7480](https://www.luogu.com.cn/problem/P7480)

### 思路

允许折返找便宜油，不能只按向右贪心。最优路线的下一次有效加油一定可选为某方向遇到的第一个更便宜站；单调栈求左右候选，建线性边数图跑 Dijkstra。

### 复杂度

时间 O(n log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long s, t;
    cin >> n >> s >> t;
    vector<pair<long long, long long>> points;
    for (int i = 0; i < n; i++) {
        long long c, x;
        cin >> c >> x;
        points.push_back({x, c});
    }
    points.push_back({t, 0});
    sort(points.begin(), points.end());
    vector<long long> x, c;
    for (auto [pos, price] : points) {
        if (!x.empty() && x.back() == pos)
            c.back() = min(c.back(), price);
        else {
            x.push_back(pos);
            c.push_back(price);
        }
    }
    int N = x.size(), start = lower_bound(x.begin(), x.end(), s) - x.begin(),
        goal = lower_bound(x.begin(), x.end(), t) - x.begin();
    vector<array<int, 2>> to(N, {-1, -1});
    vector<int> st;
    for (int i = 0; i < N; i++) {
        while (!st.empty() && c[st.back()] >= c[i])
            st.pop_back();
        if (!st.empty())
            to[i][0] = st.back();
        st.push_back(i);
    }
    st.clear();
    for (int i = N - 1; i >= 0; i--) {
        while (!st.empty() && c[st.back()] >= c[i])
            st.pop_back();
        if (!st.empty())
            to[i][1] = st.back();
        st.push_back(i);
    }
    const long long INF = 4000000000000000000LL;
    vector<long long> d(N, INF);
    priority_queue<pair<long long, int>, vector<pair<long long, int>>,
                   greater<pair<long long, int>>>
        q;
    d[start] = 0;
    q.push({0, start});
    while (!q.empty()) {
        auto [dist, v] = q.top();
        q.pop();
        if (dist != d[v])
            continue;
        if (v == goal) {
            cout << dist << '\n';
            return 0;
        }
        for (int u : to[v])
            if (u >= 0) {
                long long nd = dist + c[v] * llabs(x[v] - x[u]);
                if (nd < d[u]) {
                    d[u] = nd;
                    q.push({nd, u});
                }
            }
    }

    return 0;
}
```

### 实现提醒

起点左侧油站可能有用；下一站价格严格降低；同坐标取最低价；费用六十四位。
