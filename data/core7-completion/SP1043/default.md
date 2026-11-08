## SP1043 GSS1 - Can you answer these queries I

原题：[SP1043](https://www.luogu.com.cn/problem/SP1043)

### 思路

每段保存总和、最大非空前缀和、最大非空后缀和与最大子段和。合并时跨分界的子段必为左后缀加右前缀。

### 复杂度

建树 O(n)，每次查询 O(log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Node {
    int len = 0;
    long long sum = 0, pre = 0, suf = 0, best = 0;
};
Node merge(Node a, Node b) {
    if (!a.len)
        return b;
    if (!b.len)
        return a;
    return {a.len + b.len, a.sum + b.sum, max(a.pre, a.sum + b.pre), max(b.suf, b.sum + a.suf),
            max({a.best, b.best, a.suf + b.pre})};
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    int size = 1;
    while (size < n)
        size *= 2;
    vector<Node> t(2 * size);
    for (int i = 0; i < n; i++) {
        long long x;
        cin >> x;
        t[size + i] = {1, x, x, x, x};
    }
    for (int p = size - 1; p; p--)
        t[p] = merge(t[p * 2], t[p * 2 + 1]);
    int q;
    cin >> q;
    while (q--) {
        int l, r;
        cin >> l >> r;
        Node a, b;
        for (l += size - 1, r += size; l < r; l /= 2, r /= 2) {
            if (l & 1)
                a = merge(a, t[l++]);
            if (r & 1)
                b = merge(t[--r], b);
        }
        cout << merge(a, b).best << '\n';
    }

    return 0;
}
```

### 实现提醒

子段必须非空；有序合并；不要把负数答案初始化为 0。
