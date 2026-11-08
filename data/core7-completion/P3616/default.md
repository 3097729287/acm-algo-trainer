## P3616 富金森林公园

原题：[P3616](https://www.luogu.com.cn/problem/P3616)

### 思路

露出的石头在链上形成森林，连通块数等于点数减边数。每个石头高度贡献加一，每对相邻石头的较小高度贡献减一；水位查询转为高度不小于水位的权值和。

### 复杂度

时间 O((N+M) log(N+M))，空间 O(N+M)。

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
    vector<long long> a(n), values;
    for (auto &x : a) {
        cin >> x;
        values.push_back(x);
    }
    struct Op {
        int type, p;
        long long x;
    };
    vector<Op> ops;
    for (int i = 0; i < m; i++) {
        int type;
        cin >> type;
        if (type == 1) {
            long long B;
            cin >> B;
            ops.push_back({1, 0, B});
        } else {
            int p;
            long long x;
            cin >> p >> x;
            ops.push_back({2, p - 1, x});
            values.push_back(x);
        }
    }
    sort(values.begin(), values.end());
    values.erase(unique(values.begin(), values.end()), values.end());
    Fenwick bit(values.size());
    auto change = [&](long long h, int delta) {
        int r = lower_bound(values.begin(), values.end(), h) - values.begin() + 1;
        bit.add(r, delta);
    };
    for (int i = 0; i < n; i++) {
        change(a[i], 1);
        if (i)
            change(min(a[i - 1], a[i]), -1);
    }
    for (auto op : ops)
        if (op.type == 1) {
            int r = lower_bound(values.begin(), values.end(), op.x) - values.begin();
            cout << bit.sum(values.size()) - bit.sum(r) << '\n';
        } else {
            int p = op.p;
            change(a[p], -1);
            if (p)
                change(min(a[p - 1], a[p]), 1);
            if (p + 1 < n)
                change(min(a[p], a[p + 1]), 1);
            a[p] = op.x;
            change(a[p], 1);
            if (p)
                change(min(a[p - 1], a[p]), -1);
            if (p + 1 < n)
                change(min(a[p], a[p + 1]), -1);
        }

    return 0;
}
```

### 实现提醒

与水面持平仍可见；边贡献为负一；修改时先移除旧相邻边。
