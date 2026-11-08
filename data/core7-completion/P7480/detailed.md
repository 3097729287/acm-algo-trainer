## P7480 Reboot from Blue

原题：[P7480](https://www.luogu.com.cn/problem/P7480)

### 从问题到算法

油箱无限，若下一次购买的油价不更低，可以直接在当前站购买这部分油而不增加费用，因此有效加油价格严格下降。向某方向走时，若先遇到更便宜站，就可以先在这里改用更便宜的油，再继续后面的路线，不会变差。故只需向左右最近的严格更便宜站建边，边权为当前价乘距离。

把终点当作价格零的特殊站，到了就结束。排序位置，用两个单调栈分别找到左右严格更便宜的站；同位置合并为最低价格。每点至多两条边，Dijkstra 求起点到终点最短费用。

这个模型保留起点左侧站，也允许左右折返。例如起点油价一百、左一格油价一、终点右一百格，先向左加油费用二百零一，远好于一直向右的一万。这样的反例说明不能删掉左侧站。

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
