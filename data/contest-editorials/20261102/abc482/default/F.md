## F. Mod M Divisor

### 题意

[原题链接](https://atcoder.jp/contests/abc482/tasks/abc482_f)

给定 $N\le10^{14}$、$M\le4\times10^5$。对每个 $0\le k<M$，求最小正整数 $t$，使 $N^t$ 存在一个正约数 $x$ 满足 $x\equiv k\pmod M$；不存在输出负一。

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

分解 $N=\prod_{j=0}^{s-1}p_j^{a_j}$。一个数是 $N^t$ 的约数，当且仅当它能写成 $t$ 个 $N$ 的约数之积：将每个素因子的指数分给 $t$ 份，每份至多 $a_j$ 即可。

直接按“乘一个约数”建图的边太多。将一次乘约数拆成 $s$ 个素因子阶段，状态 $(j,r)$ 表示下一步处理 $p_j$、当前乘积余数为 $r$。选择 $0\le e\le a_j$，转移到
$$((j+1)\bmod s,\ r p_j^e\bmod M).$$
从第零阶段出发的边花费一，其他边花费零；绕一整圈恰好乘一个约数并增加一轮。

![一个约数拆成两层，指数零也是合法选择](assets/layers.svg)

从 $(0,1\bmod M)$ 做 0-1 BFS：零权松弛放队首，一权放队尾。只读取回到第零层的最短距离，就是完整轮数；起点余数的零轮答案改为一。$N=1$ 时只有约数一，单独处理。

试除分解时间 $O(\sqrt N)$，建图隐式进行，总时间 $O(\sqrt N+M\log N)$，空间 $O(Ms)$。乘法先提升到 $\verb@long long@$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    long long n;
    int m;
    cin >> n >> m;
    vector<pair<int, int>> factors;
    for (long long p = 2; p * p <= n; p += (p == 2 ? 1 : 2)) {
        if (n % p != 0) continue;
        int exponent = 0;
        while (n % p == 0) { n /= p; ++exponent; }
        factors.push_back({int(p % m), exponent});
    }
    if (n > 1) factors.push_back({int(n % m), 1});
    if (factors.empty()) {
        for (int r = 0; r < m; ++r) cout << (r == 1 % m ? 1 : -1) << '\n';
        return 0;
    }
    int layers = factors.size(), inf = 1000000000;
    vector<int> dist(layers * m, inf);
    vector<char> done(layers * m);
    deque<int> q;
    dist[1 % m] = 0; q.push_back(1 % m);
    while (!q.empty()) {
        int id = q.front(); q.pop_front();
        if (done[id]) continue;
        done[id] = 1;
        int layer = id / m, residue = id % m;
        int next_layer = (layer + 1) % layers;
        int cost = layer == 0;
        long long next_residue = residue;
        for (int e = 0; e <= factors[layer].second; ++e) {
            int to = next_layer * m + int(next_residue);
            if (dist[id] + cost < dist[to]) {
                dist[to] = dist[id] + cost;
                // 开始新一轮花费一，其余因子层不增加轮数。
                if (cost == 0) q.push_front(to); else q.push_back(to);
            }
            next_residue = next_residue * factors[layer].first % m;
        }
    }
    // 只读回到第零层的完整轮次；t 必须是正整数。
    for (int r = 0; r < m; ++r) cout << (dist[r] == inf ? -1 : max(1, dist[r])) << '\n';
}
```

### 易错点

指数零必须允许，约数一不能漏。只要完整一轮开始时加一次代价。题目求正整数轮数，起点答案是一；$N=1$ 没有素因子，须单独处理。
