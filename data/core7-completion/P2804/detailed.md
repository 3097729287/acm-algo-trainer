## P2804 神秘数字

原题：[P2804](https://www.luogu.com.cn/problem/P2804)

### 从问题到算法

子段平均值大于 M，可以同乘正的长度，得到原子段和大于 M×长度。因此逐项减去 M 后，只需统计和严格为正的子段。

定义前缀和 p[0]=0，子段 [l,r] 的新和为 p[r]−p[l−1]。它严格为正，当且仅当 p[l−1]<p[r]。从左到右扫描前缀和，在树状数组中保存此前前缀值出现次数，查询当前排名之前的总数，就得到以当前位置结尾的合法子段数。

先查询再插入，防止把当前前缀与自己配对；查询 rank−1，防止把和为零的子段计入。重复前缀值应按次数保存。答案最后对 92084931 取模。

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

    int n, m;
    cin >> n >> m;
    vector<long long> p(n + 1), values;
    for (int i = 1; i <= n; i++) {
        int x;
        cin >> x;
        p[i] = p[i - 1] + x - m;
    }
    values = p;
    sort(values.begin(), values.end());
    values.erase(unique(values.begin(), values.end()), values.end());
    Fenwick bit(values.size());
    long long ans = 0;
    for (long long x : p) {
        int rank = lower_bound(values.begin(), values.end(), x) - values.begin() + 1;
        ans += bit.sum(rank - 1);
        bit.add(rank, 1);
    }
    cout << ans % 92084931 << '\n';

    return 0;
}
```

### 实现提醒

严格小于，查询排名减一；插入 p[0]；每项先减 M。
