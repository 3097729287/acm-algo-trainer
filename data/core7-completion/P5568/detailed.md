## P5568 校门外的区间

原题：[P5568](https://www.luogu.com.cn/problem/P5568)

### 从问题到算法

将 [a,b] 编为 [2a,2b]，左开则左端加一，右开则右端减一。奇位置代表两个相邻整数间的整段开区间，因此可以同时保存端点与端点间的选中状态。

U 将 T 内置一，D 置零，S 翻转；I 清空 T 外，C 清空 T 外并翻转 T 内。空 T 对 U、D、S 无影响，对 I、C 则清空整个集合。

线段树维护赋值标记和翻转标记。赋值覆盖旧翻转，翻转若遇到已有赋值就直接改零一；否则异或翻转位。操作完成后下传得到每个加倍位置的状态，合并连续选中段，偶端点输出闭括号，奇端点输出对应整数的开括号。

### 复杂度

设坐标域 V=131071，时间 O(M log V+V)，空间 O(V)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    const int V = 131071;
    vector<int> assign(4 * V, 0);
    vector<char> flip(4 * V);
    auto apply = [&](int v, int type) {
        if (type < 2) {
            assign[v] = type;
            flip[v] = 0;
        } else if (assign[v] >= 0)
            assign[v] ^= 1;
        else
            flip[v] ^= 1;
    };
    function<void(int)> push = [&](int v) {
        if (assign[v] >= 0) {
            apply(v * 2, assign[v]);
            apply(v * 2 + 1, assign[v]);
            assign[v] = -1;
        }
        if (flip[v]) {
            apply(v * 2, 2);
            apply(v * 2 + 1, 2);
            flip[v] = 0;
        }
    };
    function<void(int, int, int, int, int, int)> update = [&](int v, int l, int r, int L, int R,
                                                              int type) {
        if (L > R)
            return;
        if (L <= l && r <= R) {
            apply(v, type);
            return;
        }
        push(v);
        int mid = (l + r) / 2;
        if (L <= mid)
            update(v * 2, l, mid, L, R, type);
        if (R > mid)
            update(v * 2 + 1, mid + 1, r, L, R, type);
    };
    char op, left, right, comma;
    int a, b;
    while (cin >> op >> left >> a >> comma >> b >> right) {
        int L = 2 * a + (left == '('), R = 2 * b - (right == ')');
        if (L > R) {
            if (op == 'I' || op == 'C')
                apply(1, 0);
            continue;
        }
        if (op == 'I' || op == 'C') {
            update(1, 0, V - 1, 0, L - 1, 0);
            update(1, 0, V - 1, R + 1, V - 1, 0);
        }
        if (op == 'U')
            update(1, 0, V - 1, L, R, 1);
        if (op == 'D')
            update(1, 0, V - 1, L, R, 0);
        if (op == 'S' || op == 'C')
            update(1, 0, V - 1, L, R, 2);
    }
    vector<char> chosen(V);
    function<void(int, int, int)> collect = [&](int v, int l, int r) {
        if (assign[v] >= 0) {
            fill(chosen.begin() + l, chosen.begin() + r + 1, assign[v]);
            return;
        }
        push(v);
        int mid = (l + r) / 2;
        collect(v * 2, l, mid);
        collect(v * 2 + 1, mid + 1, r);
    };
    collect(1, 0, V - 1);
    bool any = false;
    for (int l = 0; l < V;) {
        if (!chosen[l]) {
            l++;
            continue;
        }
        int r = l;
        while (r + 1 < V && chosen[r + 1])
            r++;
        if (any)
            cout << ' ';
        any = true;
        cout << (l % 2 ? '(' : '[') << l / 2 << ',' << (r + 1) / 2 << (r % 2 ? ')' : ']');
        l = r + 1;
    }
    if (!any)
        cout << "empty set";
    cout << '\n';

    return 0;
}
```

### 实现提醒

C 是 T−S；开端点调整一格；空区间的 I/C 清空所有内容。
