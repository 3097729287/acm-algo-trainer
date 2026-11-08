## P10814 离线二维数点

原题：[P10814](https://www.luogu.com.cn/problem/P10814)

### 从问题到算法

每个元素对应二维点 (下标,值)，询问要统计下标在 [l,r] 且值≤x 的点。离线按第二维扫描，就只剩一维区间计数。

按 x 从小到大处理，每次将尚未加入且 a[i]≤x 的位置加一，已经加入的永远不需删除。树状数组查询前 r 个位置数量减前 l−1 个，得到闭区间计数。

保存询问原编号，最后按输入次序输出。相同数值也都要在等值 x 的询问之前加入。

### 复杂度

时间 O((n+m) log(n+m))，空间 O(n+m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Fenwick {
    int n;
    vector<long long> t;
    explicit Fenwick(int n) : n(n), t(n + 1) {}
    void add(int x, long long v) {
        for (; x <= n; x += x & -x)
            t[x] += v;
    }
    long long sum(int x) const {
        long long s = 0;
        for (; x; x -= x & -x)
            s += t[x];
        return s;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<pair<int, int>> a(n);
    for (int i = 0; i < n; i++) {
        cin >> a[i].first;
        a[i].second = i + 1;
    }
    sort(a.begin(), a.end());
    struct Q {
        int l, r, x, id;
    };
    vector<Q> queries(m);
    for (int i = 0; i < m; i++) {
        cin >> queries[i].l >> queries[i].r >> queries[i].x;
        queries[i].id = i;
    }
    sort(queries.begin(), queries.end(), [](Q a, Q b) { return a.x < b.x; });
    Fenwick bit(n);
    vector<long long> ans(m);
    int p = 0;
    for (auto q : queries) {
        while (p < n && a[p].first <= q.x) {
            bit.add(a[p].second, 1);
            p++;
        }
        ans[q.id] = bit.sum(q.r) - bit.sum(q.l - 1);
    }
    for (auto x : ans)
        cout << x << '\n';

    return 0;
}
```

### 实现提醒

使用≤而非<；相同数值全部激活；答案恢复原询问顺序。
