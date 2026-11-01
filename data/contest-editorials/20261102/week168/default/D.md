## D. 小月的储物格

### 题意

[原题链接](https://ac.nowcoder.com/acm/contest/142559/D)

$n$ 个储物格构成环，起初全空，人从一号开始。每轮先沿原环走 $d_i$ 步，经过已占用格也算步数；若终点已占用，就向前找到第一个空格并占用。求占用格标签和、最后位置。$1\le m\le n\le2\times10^5$，$d_i\le10^9$，标签可为负数。

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

### 思路

每轮的原始起点是 $1+((pos-1+d_i)\bmod n)$。真正需要优化的是之后“寻找第一个空格”的过程。

用后继链接维护 $\verb@find_next(x)@$：返回编号至少为 $x$ 的第一个空格，不存在则返回哨兵 $n+1$。空格最初指向自己；占用 $x$ 后，把它指向 $\verb@find_next(x+1)@$。查找时压缩经过的链接，避免反复逐格跳过已占用部分。

![后继链接越过占用格，到哨兵后从一号重新查询](assets/successor.svg)

从原始起点查询，若得到哨兵，再查询一号，就实现环绕。最后一次全部占满后不再查询，哨兵始终保留。

路径压缩但不按秩合并，保守总时间界为 $O((n+m)\log n)$，空间 $O(n)$。标签和用 $\verb@long long@$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
vector<int> parent_link;
int find_next(int x) {
    int root = x;
    while (parent_link[root] != root) root = parent_link[root];
    // 路径压缩：以后直接跳到当前第一个可用位置。
    while (x != root) { int next = parent_link[x]; parent_link[x] = root; x = next; }
    return root;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<long long> a(n + 1);
    for (int i = 1; i <= n; ++i) cin >> a[i];
    parent_link.resize(n + 2);
    iota(parent_link.begin(), parent_link.end(), 0);
    int pos = 1;
    long long answer = 0;
    for (int turn = 0; turn < m; ++turn) {
        long long d;
        cin >> d;
        // d 按原来的 n 个格子计算，不能只在空格中数步数。
        int start = 1 + (pos - 1 + d) % n;
        pos = find_next(start);
        if (pos == n + 1) pos = find_next(1);
        answer += a[pos];
        parent_link[pos] = find_next(pos + 1);
    }
    cout << answer << ' ' << pos << '\n';
}
```

### 易错点

取模的模数始终是原来的 $n$。必须给 $n+1$ 留空间，不能读取它的标签。标签可能为负，累计和用 $\verb@long long@$。
