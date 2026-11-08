## CF438D The Child and Sequence

原题：[CF438D](https://www.luogu.com.cn/problem/CF438D)

### 从问题到算法

取模不是能直接作用于区间和的运算，例如总和相同的两段取模后可能不同。因此这里不设置取模懒标记，而利用值域缩小剪枝。

若一段最大值小于 x，所有元素都不变；否则向孩子递归，直到单点计算余数。一个正数真正发生取模变化后，会至少减半：若 x 不超过原数的一半，余数小于 x；若 x 大于一半，余数等于原数减 x，也小于一半。

所以两次赋值之间，一个数只能被有效取模 O(log A) 次。区间和查询与单点赋值按普通线段树实现，赋值可能重新增大数值，它带来的后续变化次数一并计入摊还成本。

### 复杂度

取模操作摊还总时间 O((n+q) log A log n)，查询与赋值 O(log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<long long> sum(4 * n);
    vector<int> mx(4 * n);
    auto pull = [&](int p) {
        sum[p] = sum[p * 2] + sum[p * 2 + 1];
        mx[p] = max(mx[p * 2], mx[p * 2 + 1]);
    };
    function<void(int, int, int)> build = [&](int p, int l, int r) {
        if (l == r) {
            cin >> mx[p];
            sum[p] = mx[p];
            return;
        }
        int m = (l + r) / 2;
        build(p * 2, l, m);
        build(p * 2 + 1, m + 1, r);
        pull(p);
    };
    build(1, 1, n);
    function<long long(int, int, int, int, int)> query = [&](int p, int l, int r, int a,
                                                             int b) -> long long {
        if (a <= l && r <= b)
            return sum[p];
        int m = (l + r) / 2;
        long long ans = 0;
        if (a <= m)
            ans += query(p * 2, l, m, a, b);
        if (b > m)
            ans += query(p * 2 + 1, m + 1, r, a, b);
        return ans;
    };
    function<void(int, int, int, int, int, int)> mod = [&](int p, int l, int r, int a, int b,
                                                           int x) {
        if (r < a || l > b || mx[p] < x)
            return;
        if (l == r) {
            mx[p] %= x;
            sum[p] = mx[p];
            return;
        }
        int m = (l + r) / 2;
        mod(p * 2, l, m, a, b, x);
        mod(p * 2 + 1, m + 1, r, a, b, x);
        pull(p);
    };
    function<void(int, int, int, int, int)> setvalue = [&](int p, int l, int r, int i, int x) {
        if (l == r) {
            sum[p] = mx[p] = x;
            return;
        }
        int m = (l + r) / 2;
        if (i <= m)
            setvalue(p * 2, l, m, i, x);
        else
            setvalue(p * 2 + 1, m + 1, r, i, x);
        pull(p);
    };
    while (q--) {
        int op, l, r, x;
        cin >> op >> l >> r;
        if (op == 1)
            cout << query(1, 1, n, l, r) << '\n';
        else if (op == 2) {
            cin >> x;
            mod(1, 1, n, l, r, x);
        } else
            setvalue(1, 1, n, l, r);
    }

    return 0;
}
```

### 实现提醒

最大值等于模数时仍须修改；区间和用 long long；不能直接对整段和取模。
