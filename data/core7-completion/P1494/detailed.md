## P1494 小 Z 的袜子

原题：[P1494](https://www.luogu.com.cn/problem/P1494)

### 从问题到算法

所有询问都只读取同一份静态数组，可以改变处理顺序，再按原编号输出。把左端点分成长度约 sqrt(n) 的块，同块内按右端点排序；奇偶块交替排序方向可减少右端点回跳。

维护当前闭区间 [l,r]，初始为空。要到达下一个区间，移动四个边界，每步只加入或删除一个位置，因此只有一个值的频数发生变化。若一种颜色有 c 只袜子，有序抽取两只的同色方案为 c(c−1)。全部有序方案为 len(len−1)，各颜色贡献之和除以这个分母就是所求概率。长度一或分子零时输出 0/1；其它情况用 gcd 约分。

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
        int &c = freq[a[p]];
        current -= 1LL * c * (c - 1);
        c += delta;
        current += 1LL * c * (c - 1);
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
    for (int i = 0; i < q; i++) {
        long long a = answer[i], b = length[i] * (length[i] - 1);
        if (a == 0)
            cout << "0/1\n";
        else {
            long long g = gcd(a, b);
            cout << a / g << '/' << b / g << '\n';
        }
    }
    return 0;
}
```

### 实现提醒

分子分母都用 long long；长度为一输出 0/1；不同袜子按编号区分。
