## P6834 梦原

原题：[P6834](https://www.luogu.com.cn/problem/P6834)

### 从问题到算法

把果实按高度分层，第 h 层保留所有 a[i]≥h 的点，每个连通块用一次魔法即可。所有层的连通块总数等于 Σa[i]−Σ边min(a[u],a[v])，也就是 a1+Σ(i>1)max(a[i]−a[parent],0)。

这个构造也是最优的。记上式为势能，一次对连通块减一时，点和减少块大小，内部边最小值减少块大小减一，边界的变化只会进一步降低势能的减少量，因此势能每次最多下降一。要降到零，至少需要初始势能次，按层构造恰好达到它。

利用期望线性性，第 i 项对最近 min(k,i−1) 个值取平均。若其中小于 a[i] 的数有 c 个、总和为 s，则正差之和为 a[i]c−s。离散化数值，用两棵树状数组在滑动窗口中维护数量与总和，再乘窗口长度的模逆元。

### 复杂度

时间 O(n log n)，空间 O(n)。

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

    int n, k;
    cin >> n >> k;
    const long long P = 998244353;
    vector<long long> a(n), values;
    for (auto &x : a)
        cin >> x;
    values = a;
    sort(values.begin(), values.end());
    values.erase(unique(values.begin(), values.end()), values.end());
    Fenwick count(values.size()), sum(values.size());
    vector<long long> inv(k + 1);
    inv[1] = 1;
    for (int i = 2; i <= k; i++)
        inv[i] = (P - P / i) * inv[P % i] % P;
    auto rank = [&](long long x) {
        return int(lower_bound(values.begin(), values.end(), x) - values.begin()) + 1;
    };
    auto change = [&](int i, int delta) {
        int r = rank(a[i]);
        count.add(r, delta);
        sum.add(r, a[i] * delta);
    };
    long long ans = a[0];
    change(0, 1);
    for (int i = 1; i < n; i++) {
        if (i - k - 1 >= 0)
            change(i - k - 1, -1);
        int r = rank(a[i]);
        long long positive = (a[i] * count.sum(r - 1) - sum.sum(r - 1)) % P;
        ans = (ans + positive * inv[min(k, i)]) % P;
        change(i, 1);
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

差取正部后再求平均；旧父亲离开窗口时删除；a 可以为零。
