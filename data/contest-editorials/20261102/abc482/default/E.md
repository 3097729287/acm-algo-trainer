## E. Diameter Endpoint Colors

### 题意

[原题链接](https://atcoder.jp/contests/abc482/tasks/abc482_e)

给定 $N$ 点无权树及每点颜色 $C_v$，统计同色无序点对 $u<v$，要求两点距离恰好为整棵树的直径。$2\le N\le2\times10^5$，$1\le C_v\le N$。

### 从零讲：queue、deque 与 stack：处理顺序也是规则

<details>
<summary>展开可复用的基础知识</summary>

#### queue、deque 与 stack：处理顺序也是规则

$\verb@queue@$ 是先进先出：先进入的先处理，适合按层扩展；$\verb@stack@$ 是后进先出：最后放入的先处理，适合嵌套配对与回退；$\verb@deque@$ 支持两端加入删除，适合滑动窗口和 0-1 BFS。它们不能按方便程度随意互换，处理顺序会影响算法成立的理由。

```cxx
queue<int> q;
q.push(3); q.push(5);
int first = q.front(); // 3
q.pop();              // 删除 3，pop 不返回元素
stack<int> st;
st.push(3); st.push(5);
int last = st.top();   // 5
st.pop();
```

$\verb@deque@$ 的接口是 $\verb@push_back@$、$\verb@push_front@$、$\verb@pop_back@$、$\verb@pop_front@$、$\verb@front@$、$\verb@back@$。在常用默认底层容器下，这些端点操作为常数时间；保存 $n$ 项需要 $O(n)$ 空间。$\verb@stack@$ 和 $\verb@queue@$ 是限制了接口的适配器，也可选择其它底层容器。

任何 $\verb@front@$、$\verb@back@$、$\verb@top@$ 或弹出操作前都须保证非空；先读元素再弹出。遍历图时，容器只规定“谁先处理”，仍需另存访问标记；若不限制同一个状态反复入队，有限图也可能无限重复处理。


</details>

### 从零讲：vector：长度可变的连续数组

<details>
<summary>展开可复用的基础知识</summary>

#### vector：长度可变的连续数组

$\verb@vector<T>@$ 保存一串同类型的元素，适合按下标访问、扫描、排序。$\verb@T@$ 是元素类型，例如 $\verb@vector<int>@$ 保存整数，$\verb@vector<pair<int,int>>@$ 保存整数对，$\verb@vector<vector<int>>@$ 可保存每个顶点各自的邻居。需要 $\verb@<vector>@$。

```cxx
vector<int> a(3, 7);   // 三个元素，内容是 7、7、7
a.push_back(9);       // 在末尾追加，现在长度为 4
int x = a[1];         // 从 0 编号，这里得到 7
a[1] = 2;            // 改第二个元素
int n = int(a.size());
```

$\verb@vector<int> a(3)@$ 创建三个值为零的元素；$\verb@a.reserve(3)@$ 只预留容量，元素数仍为零，此时不能访问 $\verb@a[0]@$。长度 $\verb@size()@$ 与容量 $\verb@capacity()@$ 是不同概念。

下标访问为 $O(1)$，遍历为 $O(n)$。末尾追加通常为 $O(1)$；容量不足时会分配更大的连续空间并搬移元素，这次可能为 $O(n)$，一连串追加的平均成本称为摊还 $O(1)$。中间插入或删除会搬移后续元素，最坏 $O(n)$。内存是元素量的 $O(n)$，并可能预留部分尚未使用的容量。

$\verb@begin()@$ 指向首元素，$\verb@end()@$ 指向尾后位置，$\verb@sort(a.begin(),a.end())@$ 操作整个数组。$\verb@a[i]@$ 不检查越界；下标须满足 $0\le i<\mathrm{size}$。$\verb@at(i)@$ 会检查越界并抛异常。空数组不能访问 $\verb@front()@$、$\verb@back()@$；$\verb@pop_back()@$ 也要求非空。

扩容后指向旧存储的迭代器、引用和指针会失效。遍历的同时 $\verb@push_back@$，不能假定此前取得的引用仍可用。读取大数组的函数常用 $\verb@const vector<int>& a@$ 按常量引用传入，既不复制也禁止通过该引用修改；$\verb@vector<int> a@$ 按值传参则复制内容。选择副本还是引用取决于是否要保留独立数据。


</details>

### 从零讲：整数类型、整除与溢出

<details>
<summary>展开可复用的基础知识</summary>

#### 整数类型、整除与溢出

计算前先看每一步可能达到的范围。常见环境中 $\verb@int@$ 是 32 位，上界约 $2.1\times10^9$；$\verb@long long@$ 至少 64 位，常见有符号 64 位上界约 $9.22\times10^{18}$。$\verb@using ll = long long;@$ 只是为已有类型起别名。

```cxx
int a = 100000, b = 100000;
long long wrong = a * b;      // 右边先按 int 乘，可能已溢出
long long right = 1LL * a * b; // 先把运算提升到 long long
```

不能指望“接收结果的变量够大”修复此前已经溢出的计算。先提高操作数类型，再做乘法。超过 64 位时，GCC 的 $\verb@__int128@$ 可作中间量，但它不是标准 C++17 类型，也没有标准流输出重载；先证明范围，再选择工具。

整数 $\verb@/@$ 对有符号数向零截断：$\verb@7/3==2@$、$\verb@-7/3==-2@$。对非负数才等于向下取整。余数满足 $\verb@a == (a/b)*b + a%b@$，除数不能为零；要将余数归入 $[0,m-1]$（$m>0$），可用 $\verb@(a % m + m) % m@$，同时保证中间加法不溢出。

非负 $a$、正 $b$ 的向上取整可写 $\verb@a/b + (a%b != 0)@$，比 $\verb@(a+b-1)/b@$ 更容易避免加法溢出。比较平方时也应在宽类型内计算；浮点数不适合作为大整数相等的默认判断方式。

$\verb@size()@$ 返回无符号类型。空容器上写 $\verb@size()-1@$ 会绕到很大的数，逆序遍历可以先转成有符号、确认长度，或使用逆向迭代器。$\verb@abs@$ 对最小有符号数无法在同类型中表达其正值，需先约束输入差值范围。一般机器整数运算按常数时间估算，宽类型解决表示范围，不改变算法的增长阶。


</details>

### 思路

先用两次 BFS 找到一条直径及其长度 $D$，沿第二次 BFS 的父指针恢复直径路径，从而找到树中心。

![直径奇偶性决定中心是一个点还是一条边](assets/diameter.svg)

若 $D=2r$，中心是一个点。直径两端必须位于不同中心分支，且都距中心 $r$。逐分支收集这一深度的端点颜色：先将本分支每个颜色与先前分支的同色数量配对，再将本分支整批加入计数。这样每对恰好计一次，且不会误计同分支。

若 $D=2r+1$，中心是相邻两点。删除中心边，分别统计两侧距各自中心 $r$ 的端点；相同颜色的左右数量相乘求和。

两种情况下距离都恰好为 $D$，也覆盖全部直径端点。总时间 $O(N)$，空间 $O(N)$；答案用 $\verb@long long@$，遍历使用队列或显式栈，避免长链递归溢出。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
int farthest(int start, const vector<vector<int>> &g, vector<int> &dist, vector<int> &parent) {
    int n = g.size();
    dist.assign(n, -1); parent.assign(n, -1);
    queue<int> q;
    q.push(start); dist[start] = 0;
    int best = start;
    while (!q.empty()) {
        int v = q.front(); q.pop();
        if (dist[v] > dist[best]) best = v;
        for (int u : g[v]) if (dist[u] == -1) {
            dist[u] = dist[v] + 1; parent[u] = v; q.push(u);
        }
    }
    return best;
}
vector<int> endpoint_colors(int root, int blocked, int depth, int target,
                            const vector<vector<int>> &g, const vector<int> &color) {
    vector<int> result;
    vector<array<int, 3>> st = {{root, blocked, depth}};
    while (!st.empty()) {
        auto item = st.back(); st.pop_back();
        int v = item[0], parent = item[1], d = item[2];
        if (d == target) { result.push_back(color[v]); continue; }
        for (int u : g[v]) if (u != parent) st.push_back({u, v, d + 1});
    }
    return result;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<vector<int>> g(n);
    for (int i = 1, u, v; i < n; ++i) { cin >> u >> v; --u; --v; g[u].push_back(v); g[v].push_back(u); }
    vector<int> color(n);
    for (int &c : color) cin >> c;
    vector<int> dist, parent;
    int a = farthest(0, g, dist, parent);
    int b = farthest(a, g, dist, parent);
    int diameter = dist[b], radius = diameter / 2;
    vector<int> path;
    for (int v = b; v != -1; v = parent[v]) path.push_back(v);
    vector<long long> seen(n + 1);
    long long answer = 0;
    if (diameter % 2 == 1) {
        int left = path[radius], right = path[radius + 1];
        for (int c : endpoint_colors(left, right, 0, radius, g, color)) ++seen[c];
        for (int c : endpoint_colors(right, left, 0, radius, g, color)) answer += seen[c];
    } else {
        int center = path[radius];
        for (int u : g[center]) {
            vector<int> group = endpoint_colors(u, center, 1, radius, g, color);
            // 当前分支只与先前分支配对，避免同分支误计。
            for (int c : group) answer += seen[c];
            for (int c : group) ++seen[c];
        }
    }
    cout << answer << '\n';
}
```

### 易错点

偶数直径必须排除同分支点对，整批查询后再整批加入。奇数直径按中心边分左右。直径长度是边数；$N=2$ 对应半径零，也应统计两侧中心本身。
