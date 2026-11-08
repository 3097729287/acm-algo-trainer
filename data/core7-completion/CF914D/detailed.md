## CF914D Bash and a Tough Math Puzzle

原题：[CF914D](https://www.luogu.com.cn/problem/CF914D)

### 从问题到算法

题目允许把一个数改成任意整数。如果区间只有零个或一个不被 x 整除的数，就能让整段 gcd 为 x 的倍数；若有两个坏数，一次修改不能同时修复。因此查询转化为坏数计数。

一段所有数都能被 x 整除，当且仅当它们的 gcd 能被 x 整除。线段树保存每段 gcd，遇到能够整除的整段无需继续往下；否则分解，直到叶子确认一个坏数。坏数达到两个立即返回，不再遍历更多节点。

每层至多沿着两个坏点的路径深入，因此查询仍是对数复杂度。单点修改后沿祖先重新计算 gcd。注意这里只判断能否通过修改实现整除关系，不要求原区间 gcd 恰好等于 x。

### 复杂度

每次操作 O(log n·log A)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> t(4 * n);
    function<void(int, int, int)> build = [&](int p, int l, int r) {
        if (l == r) {
            cin >> t[p];
            return;
        }
        int m = (l + r) / 2;
        build(p * 2, l, m);
        build(p * 2 + 1, m + 1, r);
        t[p] = gcd(t[p * 2], t[p * 2 + 1]);
    };
    build(1, 1, n);
    function<void(int, int, int, int, int)> change = [&](int p, int l, int r, int x, int v) {
        if (l == r) {
            t[p] = v;
            return;
        }
        int m = (l + r) / 2;
        if (x <= m)
            change(p * 2, l, m, x, v);
        else
            change(p * 2 + 1, m + 1, r, x, v);
        t[p] = gcd(t[p * 2], t[p * 2 + 1]);
    };
    function<void(int, int, int, int, int, int, int &)> bad = [&](int p, int l, int r, int a, int b,
                                                                  int x, int &count) {
        if (count >= 2 || r < a || l > b || t[p] % x == 0)
            return;
        if (l == r) {
            count++;
            return;
        }
        int m = (l + r) / 2;
        bad(p * 2, l, m, a, b, x, count);
        bad(p * 2 + 1, m + 1, r, a, b, x, count);
    };
    int q;
    cin >> q;
    while (q--) {
        int op;
        cin >> op;
        if (op == 1) {
            int l, r, x, c = 0;
            cin >> l >> r >> x;
            bad(1, 1, n, l, r, x, c);
            cout << (c <= 1 ? "YES" : "NO") << '\n';
        } else {
            int p, x;
            cin >> p >> x;
            change(1, 1, n, p, x);
        }
    }

    return 0;
}
```

### 实现提醒

找到两个坏点就停止；剪枝条件是 gcd % x == 0；更新是赋值。
