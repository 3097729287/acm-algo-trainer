## P2709 莫队 / 小 B 的询问

原题：[P2709](https://www.luogu.com.cn/problem/P2709)

### 思路

把询问离线排序，让相邻询问的区间端点缓慢移动。维护每个值的出现次数，每次只增删一个位置，常数时间更新答案。某个数的频数从 c 改为 c+delta 时，它的贡献从 c² 变为 (c+delta)²。先减旧平方再加新平方，即可在常数时间更新整个答案。

### 复杂度

时间 O((n+q)sqrt n)，空间 O(n+q)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    int k;
    cin >> k;
    vector<int> a(n + 1), values;
    for (int i = 1; i <= n; i++) {
        cin >> a[i];
        values.push_back(a[i]);
    }
    sort(values.begin(), values.end());
    values.erase(unique(values.begin(), values.end()), values.end());
    for (int i = 1; i <= n; i++)
        a[i] = lower_bound(values.begin(), values.end(), a[i]) - values.begin();

    struct Query {
        int l, r, id;
    };
    vector<Query> queries(q);
    for (int i = 0; i < q; i++) {
        cin >> queries[i].l >> queries[i].r;
        queries[i].id = i;
    }
    int block = max(1, (int)sqrt(n));
    sort(queries.begin(), queries.end(), [&](Query a, Query b) {
        if (a.l / block != b.l / block)
            return a.l < b.l;
        return (a.l / block) & 1 ? a.r > b.r : a.r < b.r;
    });

    vector<int> freq(values.size());
    vector<long long> answer(q), length(q);
    long long current = 0;
    auto change = [&](int p, int delta) {
        int &c = freq[a[p]];
        current -= 1LL * c * c;
        c += delta;
        current += 1LL * c * c;
    };
    int l = 1, r = 0;
    for (auto query : queries) {
        while (l > query.l)
            change(--l, 1);
        while (r < query.r)
            change(++r, 1);
        while (l < query.l)
            change(l++, -1);
        while (r > query.r)
            change(r--, -1);
        answer[query.id] = current;
        length[query.id] = query.r - query.l + 1;
    }
    for (long long x : answer)
        cout << x << '\n';
    return 0;
}
```

### 实现提醒

平方运算先转 long long；k 是值域上限，不是查询数量。
