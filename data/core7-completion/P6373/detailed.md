## P6373 IOI 计数

原题：[P6373](https://www.luogu.com.cn/problem/P6373)

### 从问题到算法

题目要求下标递增，不要求字符连续，因此一个区间的计数需要记录可以与另一段拼接的短子序列。除了单字符 I、O，还要记录 IO、OI 以及完整的 IOI。

合并左右两段时，IO 的跨界贡献为左 I 数乘右 O 数；OI 类似。IOI 要么完全在某一边，要么第一个字符在左边、后两个在右边，或前两个在左边、最后一个在右边。于是跨界贡献为左 I×右 OI+左 IO×右 I。

这两类按跨界前字符数划分，互不重叠且覆盖所有可能。单点修改只改变一个叶子，再沿祖先合并。查询采用左右两个累积节点，始终按原字符串顺序拼接。三元组数可达 O(n³)，所有计数都用 long long。

### 复杂度

建树 O(n)，每次操作 O(log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Node {
    long long i = 0, o = 0, io = 0, oi = 0, ioi = 0;
};
Node leaf(char c) {
    Node a;
    a.i = c == 'I';
    a.o = c == 'O';
    return a;
}
Node merge(Node a, Node b) {
    return {a.i + b.i, a.o + b.o, a.io + b.io + a.i * b.o, a.oi + b.oi + a.o * b.i,
            a.ioi + b.ioi + a.i * b.oi + a.io * b.i};
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    string s;
    cin >> n >> m >> s;
    int size = 1;
    while (size < n)
        size *= 2;
    vector<Node> t(2 * size);
    for (int i = 0; i < n; i++)
        t[size + i] = leaf(s[i]);
    for (int p = size - 1; p; p--)
        t[p] = merge(t[p * 2], t[p * 2 + 1]);
    while (m--) {
        int op, l;
        cin >> op >> l;
        if (op == 1) {
            char c;
            cin >> c;
            int p = size + l - 1;
            t[p] = leaf(c);
            for (p /= 2; p; p /= 2)
                t[p] = merge(t[p * 2], t[p * 2 + 1]);
        } else {
            int r;
            cin >> r;
            Node a, b;
            for (l += size - 1, r += size; l < r; l /= 2, r /= 2) {
                if (l & 1)
                    a = merge(a, t[l++]);
                if (r & 1)
                    b = merge(t[--r], b);
            }
            cout << merge(a, b).ioi << '\n';
        }
    }

    return 0;
}
```

### 实现提醒

统计子序列；合并顺序不能交换；乘法和计数使用六十四位整数。
