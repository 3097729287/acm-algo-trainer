## SP30906 ADAUNIQ - Ada and Unique Vegetable

原题：[SP30906](https://www.luogu.com.cn/problem/SP30906)

### 从问题到算法

普通莫队要求数组不变，本题增加了单点修改，所以还需要时间维度。先顺序读入操作，为每次修改保存位置、修改前的值与修改后的值；每次查询记录此前已有多少次修改。

按左块、右块、时间排序，块长取约 n^(2/3)。处理查询时，先把当前数组推进或回退到它对应的时间；若被改位置在当前区间中，先删除旧值贡献，赋新值后再加入新贡献。若在区间之外，只改数组。随后像普通莫队一样移动左右端点。

贡献函数是 [freq==1]。每次修改一个频数，先减去它旧的单次出现贡献，再加上新贡献。

在读入时使用 working 数组保存修改前的值，真正执行莫队时另用初始数组。重复修改同一位置也能够准确撤销。

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
        int op, l, r;
        cin >> op >> l >> r;
        if (op == 1) {
            changes.push_back({l, working[l], r});
            working[l] = r;
        } else
            queries.push_back({l, r, (int)changes.size(), (int)queries.size()});
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
        current -= freq[x] == 1;
        freq[x] += delta;
        current += freq[x] == 1;
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
