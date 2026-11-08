## SP1684 FREQUENT - Frequent values

原题：[SP1684](https://www.luogu.com.cn/problem/SP1684)

### 从问题到算法

如果数组无序，最高频次不能仅靠左右段的最大频次合并；但本题数组非降，同值必连续，因此最高频次就是最长等值连续段。

节点记录长度、首尾值、最长等值前缀、后缀以及最佳段。合并时，若左末值等于右首值，跨界候选为左后缀加右前缀；否则最佳只可能完全位于一侧。前缀只有在整个左段同值且边界相同时才能延长，后缀同理。

区间查询保持从左到右的顺序。空节点长度为零，合并时直接返回另一边，方便处理查询边界。输入以 n=0 结束。

### 复杂度

每组建树 O(n)，每次查询 O(log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Node {
    int len = 0, first = 0, last = 0, pre = 0, suf = 0, best = 0;
};
Node merge(Node a, Node b) {
    if (!a.len)
        return b;
    if (!b.len)
        return a;
    Node c = {a.len + b.len, a.first, b.last, a.pre, b.suf, max(a.best, b.best)};
    if (a.last == b.first) {
        c.best = max(c.best, a.suf + b.pre);
        if (a.pre == a.len)
            c.pre = a.len + b.pre;
        if (b.suf == b.len)
            c.suf = b.len + a.suf;
    }
    return c;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    while (cin >> n && n) {
        cin >> q;
        int size = 1;
        while (size < n)
            size *= 2;
        vector<Node> t(2 * size);
        for (int i = 0; i < n; i++) {
            int x;
            cin >> x;
            t[size + i] = {1, x, x, 1, 1, 1};
        }
        for (int p = size - 1; p; p--)
            t[p] = merge(t[p * 2], t[p * 2 + 1]);
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
    }

    return 0;
}
```

### 实现提醒

依赖数组有序；查询必须保持拼接次序；n=0 结束。
