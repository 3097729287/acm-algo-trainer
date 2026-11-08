## P6748 Fallen Lord

原题：[P6748](https://www.luogu.com.cn/problem/P6748)

### 从问题到算法

上中位数不超过 a[u]，等价于至少 floor(deg/2)+1 条边≤a[u]，也就是超标边最多 H=floor((deg−1)/2)。

令 dp[u][state] 为 u 子树边权和最优值，state 表示父边是否>a[u]，父边本身的权值由父亲计入。处理孩子 v 时，子树费用只取决于边权是否>a[v]。因此该边最优值只可能是 a[u]、a[v] 或 m：两处阈值之间提高权值不改变状态，直到下一个阈值或上界。

对这三个候选，分别求“不超 u 阈值”的最好 L 与“超 u 阈值”的最好 R。先全部选 L，再将正收益 R−L 降序排列；父边状态零可取前 H 个，状态一可取前 H−1 个。某状态名额为负就不可行。

给定 a≥1 时全边权一已经可行，但代码仍保留不可行状态。后序计算采用迭代遍历，避免五十万点递归溢出。

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
    long long m;
    cin >> n >> m;
    vector<long long> a(n);
    for (auto &x : a)
        cin >> x;
    vector<vector<int>> g(n);
    for (int i = 1; i < n; i++) {
        int u, v;
        cin >> u >> v;
        u--;
        v--;
        g[u].push_back(v);
        g[v].push_back(u);
    }
    vector<int> parent(n, -1), order = {0};
    parent[0] = 0;
    for (int i = 0; i < n; i++)
        for (int u : g[order[i]])
            if (parent[u] < 0) {
                parent[u] = order[i];
                order.push_back(u);
            }
    const long long NEG = -(1LL << 60);
    vector<array<long long, 2>> dp(n, {NEG, NEG});
    for (int i = n - 1; i >= 0; i--) {
        int v = order[i], H = ((int)g[v].size() - 1) / 2;
        long long base = 0;
        vector<long long> gains;
        for (int u : g[v])
            if (parent[u] == v) {
                long long low = NEG, high = NEG;
                for (long long w : {a[v], a[u], m}) {
                    long long sub = dp[u][w > a[u]];
                    if (sub == NEG)
                        continue;
                    if (w <= a[v])
                        low = max(low, w + sub);
                    else
                        high = max(high, w + sub);
                }
                base += low;
                if (high > low)
                    gains.push_back(high - low);
            }
        sort(gains.rbegin(), gains.rend());
        vector<long long> prefix(gains.size() + 1);
        for (int j = 0; j < (int)gains.size(); j++)
            prefix[j + 1] = prefix[j] + gains[j];
        for (int state = 0; state < 2; state++)
            if (H >= state)
                dp[v][state] = base + prefix[min((int)gains.size(), H - state)];
    }
    cout << (dp[0][0] == NEG ? -1 : dp[0][0]) << '\n';

    return 0;
}
```

### 实现提醒

中位数为上中位数；父边也占超标名额；候选值按两端阈值分类。
