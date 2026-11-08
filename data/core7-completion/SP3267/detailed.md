## SP3267 DQUERY - D-query

原题：[SP3267](https://www.luogu.com.cn/problem/SP3267)

### 从问题到算法

固定已扫描前缀 1 到 r，对于每个出现过的值，仅保留最后一次出现位置的标记。某个值在 [l,r] 出现，当且仅当它在前缀内的最后位置不小于 l。因此查询区间的标记数恰好等于不同值数。

按 r 从小到大处理询问，每向右扫描一个数，就把它旧位置的标记减一、新位置加一，再更新 last。树状数组支持单点加减与前缀求和，sum(r)−sum(l−1) 得到区间标记数。

询问保存原编号，离线排序只改变处理次序。数值最高一百万，可以直接用 last 数组；标记树按下标长度 n 开空间。

### 复杂度

时间 O((n+q) log n+q log q)，空间 O(n+q+A)。

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

    int n;
    cin >> n;
    vector<int> a(n + 1);
    int limit = 0;
    for (int i = 1; i <= n; i++) {
        cin >> a[i];
        limit = max(limit, a[i]);
    }
    int q;
    cin >> q;
    struct Query {
        int l, r, id;
    };
    vector<Query> queries(q);
    for (int i = 0; i < q; i++) {
        cin >> queries[i].l >> queries[i].r;
        queries[i].id = i;
    }
    sort(queries.begin(), queries.end(), [](Query a, Query b) { return a.r < b.r; });
    vector<int> last(limit + 1), ans(q);
    Fenwick bit(n);
    int next = 1;
    for (auto x : queries) {
        while (next <= x.r) {
            int value = a[next];
            if (last[value])
                bit.add(last[value], -1);
            bit.add(next, 1);
            last[value] = next;
            next++;
        }
        ans[x.id] = bit.sum(x.r) - bit.sum(x.l - 1);
    }
    for (int x : ans)
        cout << x << '\n';

    return 0;
}
```

### 实现提醒

旧标记要删除；last 按数值，树状数组按位置；按原询问顺序输出。
