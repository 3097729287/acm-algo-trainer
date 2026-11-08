## P3120 Cow Hopscotch G

原题：[P3120](https://www.luogu.com.cn/problem/P3120)

### 从问题到算法

dp[i][j] 是到达该格的方案数，合法前驱必须行、列都更小且颜色不同。因此它等于左上矩形全部 dp 之和减同色 dp 之和。

用扫描行处理第一维，全局 Fenwick 按列维护所有早先行的贡献。每种颜色另有一棵 Fenwick，但只为该颜色出现的列离散化分配空间，全部颜色的节点总数不超过网格大小。

当前行每格只查询列 j−1 之前，计算后暂存；整行全部算完再加入结构，这样不会把同一行当作前驱。起点单独设一，其它首行首列自然为零。

### 复杂度

时间 O(RC log C)，空间 O(RC+K)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Bit {
    vector<int> t;
    Bit(int n) : t(n + 1) {}
    void add(int x, int v) {
        for (; x < (int)t.size(); x += x & -x) {
            t[x] += v;
            if (t[x] >= 1000000007)
                t[x] -= 1000000007;
        }
    }
    int sum(int x) const {
        int r = 0;
        for (; x; x -= x & -x) {
            r += t[x];
            if (r >= 1000000007)
                r -= 1000000007;
        }
        return r;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int R, C, K;
    cin >> R >> C >> K;
    vector<vector<int>> a(R, vector<int>(C)), columns(K + 1);
    for (int i = 0; i < R; i++)
        for (int j = 0; j < C; j++) {
            cin >> a[i][j];
            columns[a[i][j]].push_back(j + 1);
        }
    vector<Bit> colored;
    colored.reserve(K + 1);
    for (int c = 0; c <= K; c++) {
        auto &v = columns[c];
        sort(v.begin(), v.end());
        v.erase(unique(v.begin(), v.end()), v.end());
        colored.emplace_back(v.size());
    }
    Bit all(C);
    vector<int> row(C);
    int ans = 0;
    for (int i = 0; i < R; i++) {
        for (int j = 0; j < C; j++) {
            int c = a[i][j],
                r = lower_bound(columns[c].begin(), columns[c].end(), j + 1) - columns[c].begin();
            row[j] = (all.sum(j) - colored[c].sum(r) + 1000000007) % 1000000007;
            if (i == 0 && j == 0)
                row[j] = 1;
        }
        for (int j = 0; j < C; j++) {
            int c = a[i][j], r = lower_bound(columns[c].begin(), columns[c].end(), j + 1) -
                                 columns[c].begin() + 1;
            all.add(j + 1, row[j]);
            colored[c].add(r, row[j]);
        }
        ans = row[C - 1];
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

行列必须都严格增加；同色贡献相减后规范化；同一行延迟更新。
