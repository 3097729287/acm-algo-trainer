## UVA12345 Dynamic len(set(a[L:R]))

原题：[UVA12345](https://www.luogu.com.cn/problem/UVA12345)

### 思路

把每次查询记录为左端、右端和此前修改次数。离线排序后，移动两个区间端点以及时间指针，维护当前各值频数，统计频数大于 0 的值数。查询使用从 0 开始的左闭右开区间。

### 复杂度

时间 O((n+q)·n^(2/3))，空间 O(n+q+A)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Change {
    int position, before, after;
};
struct Query {
    int l, r, time, id;
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<int> a(n), working;
    for (int &x : a)
        cin >> x;
    working = a;
    vector<Change> changes;
    vector<Query> queries;
    for (int i = 0; i < q; i++) {
        char op;
        int l, r;
        cin >> op >> l >> r;
        if (op == 'M') {
            changes.push_back({l, working[l], r});
            working[l] = r;
        } else
            queries.push_back({l, r - 1, (int)changes.size(), (int)queries.size()});
    }
    int limit = 0;
    for (int x : a)
        limit = max(limit, x);
    for (auto c : changes)
        limit = max(limit, c.after);
    int block = max(1, (int)pow(n, 2.0 / 3));
    sort(queries.begin(), queries.end(), [&](Query a, Query b) {
        if (a.l / block != b.l / block)
            return a.l < b.l;
        if (a.r / block != b.r / block)
            return a.r < b.r;
        return a.time < b.time;
    });
    vector<int> freq(limit + 1), answer(queries.size());
    int current = 0, l = 0, r = -1, time = 0;
    auto adjust = [&](int x, int delta) {
        current -= freq[x] > 0;
        freq[x] += delta;
        current += freq[x] > 0;
    };
    auto apply = [&](Change c, bool forward) {
        if (l <= c.position && c.position <= r)
            adjust(a[c.position], -1);
        a[c.position] = forward ? c.after : c.before;
        if (l <= c.position && c.position <= r)
            adjust(a[c.position], 1);
    };
    for (auto query : queries) {
        while (time < query.time) {
            apply(changes[time], true);
            time++;
        }
        while (time > query.time) {
            time--;
            apply(changes[time], false);
        }
        while (l > query.l)
            adjust(a[--l], 1);
        while (r < query.r)
            adjust(a[++r], 1);
        while (l < query.l)
            adjust(a[l++], -1);
        while (r > query.r)
            adjust(a[r--], -1);
        answer[query.id] = current;
    }
    for (int x : answer)
        cout << x << '\n';

    return 0;
}
```

### 实现提醒

修改须保存旧值；时间撤销要对称；下标从 0 开始。
