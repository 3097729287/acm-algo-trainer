## CF617E XOR and Favorite Number

原题：[CF617E](https://www.luogu.com.cn/problem/CF617E)

### 思路

定义前缀异或 p，子区间异或等于 k 等价于两个前缀值异或为 k。把 [l,r] 改为前缀下标区间 [l−1,r]，用莫队维护其中符合条件的不同下标对数。

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
