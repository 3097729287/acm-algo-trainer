## CF220B Little Elephant and Array

原题：[CF220B](https://www.luogu.com.cn/problem/CF220B)

### 从问题到算法

所有询问都只读取同一份静态数组，可以改变处理顺序，再按原编号输出。把左端点分成长度约 sqrt(n) 的块，同块内按右端点排序；奇偶块交替排序方向可减少右端点回跳。

维护当前闭区间 [l,r]，初始为空。要到达下一个区间，移动四个边界，每步只加入或删除一个位置，因此只有一个值的频数发生变化。一个值 x 的贡献是 freq[x]==x。修改它的频数前，先减去旧贡献，修改后再加入新贡献。其它数的贡献完全不变。

数组值先离散化，频数按压缩下标保存，原数值另存以便需要时比较。左右端点总移动量为 O((n+q)sqrt(n))，每步修改是 O(1)。结果存到询问的原始编号位置。

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
