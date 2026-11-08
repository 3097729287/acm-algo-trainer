## CF220B Little Elephant and Array

原题：[CF220B](https://www.luogu.com.cn/problem/CF220B)

### 思路

把询问离线排序，让相邻询问的区间端点缓慢移动。维护每个值的出现次数，每次只增删一个位置，常数时间更新答案。一个值 x 的贡献是 freq[x]==x。修改它的频数前，先减去旧贡献，修改后再加入新贡献。其它数的贡献完全不变。

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
        int x = a[p];
        current -= freq[x] == values[x];
        freq[x] += delta;
        current += freq[x] == values[x];
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

数值和压缩下标不能混淆；值大于 n 时永远不会贡献。
