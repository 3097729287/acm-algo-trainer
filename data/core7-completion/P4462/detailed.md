## P4462 异或序列

原题：[P4462](https://www.luogu.com.cn/problem/P4462)

### 从问题到算法

前缀异或满足 a[x] xor … xor a[y]=p[y] xor p[x−1]。因此原查询 [l,r] 中的每个非空子区间，唯一对应前缀下标区间 [l−1,r] 内的一对不同下标。异或关系对两端对称，每对下标按原位置顺序恰好对应一个子区间。

维护当前前缀值频数。加入一个值 v 时，它与已有的 v xor k 各形成一对，所以先把该频数加到答案，再增加 v 的频数。删除时顺序相反：先减少 v 的频数，再减去剩下的 v xor k 数量。k=0 时这种顺序能避免将下标与自己配对。

把所有 p[i] 与 p[i] xor k 一起离散化，避免依赖原始值域上界。莫队只移动区间端点，答案使用六十四位整数。

### 复杂度

时间 O((n+q)sqrt n+n log n)，空间 O(n+q)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q, k;
    cin >> n >> q >> k;
    vector<int> p(n + 1), values;
    for (int i = 1, x; i <= n; i++) {
        cin >> x;
        p[i] = p[i - 1] ^ x;
    }
    for (int v : p) {
        values.push_back(v);
        values.push_back(v ^ k);
    }
    sort(values.begin(), values.end());
    values.erase(unique(values.begin(), values.end()), values.end());
    vector<int> id(n + 1), partner(n + 1);
    for (int i = 0; i <= n; i++) {
        id[i] = lower_bound(values.begin(), values.end(), p[i]) - values.begin();
        partner[i] = lower_bound(values.begin(), values.end(), p[i] ^ k) - values.begin();
    }

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
    vector<long long> ans(q);
    long long current = 0;
    auto add = [&](int i) {
        current += freq[partner[i]];
        freq[id[i]]++;
    };
    auto remove = [&](int i) {
        freq[id[i]]--;
        current -= freq[partner[i]];
    };
    int l = 0, r = -1;
    for (auto x : queries) {
        x.l--;
        while (l > x.l)
            add(--l);
        while (r < x.r)
            add(++r);
        while (l < x.l)
            remove(l++);
        while (r > x.r)
            remove(r--);
        ans[x.id] = current;
    }
    for (long long x : ans)
        cout << x << '\n';

    return 0;
}
```

### 实现提醒

左端要减一；包含 p[0]=0；删除先减频次，尤其注意 k=0。
