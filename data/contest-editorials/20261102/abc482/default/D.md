## D. Wannabe Zombie

### 题意

[原题链接](https://atcoder.jp/contests/abc482/tasks/abc482_d)

$N$ 个人位于严格递增的偶数坐标 $X_i$。初始仅第 $k$ 人感染；所有人及感染者均能以不超过一的速度自由移动，同位置接触就传播。对每个 $k$，求所有人感染的最短时间。$N\le2\times10^5$，$0\le X_i\le10^9$。

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

只需考虑先感染左邻居或右邻居。人相遇后可以互换未来行走轨迹，接触与感染位置不变，因此可以保持编号从左到右不交错，第一次新感染必然能选为邻居。

先感染左邻居时，让编号小于 $k$ 的人持续右行，其余人持续左行。相遇后两位感染者继续原方向，就分别传播到两端，完成时间为
$$T_L=\frac{\max(X_k-X_1,\ X_N-X_{k-1})}{2}.$$
这是最优的：左端与初始传播源的距离每秒至多缩短二；右端的传播要经过第一次接触，而接触点在时刻 $\tau$ 至多为 $X_{k-1}+\tau$，故感染前沿在时刻 $T$ 至多到 $X_{k-1}+T$，同样给出第二个下界。

![先向右感染邻居的具体轨迹，分别在四、七时刻到达两端](assets/zombie.svg)

先感染右邻居对称得到
$$T_R=\frac{\max(X_{k+1}-X_1,\ X_N-X_k)}{2}.$$
取存在的方案中较小值。端点只考虑唯一邻居，$N=1$ 答案零。时间 $O(N)$，空间 $O(N)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<long long> x(n);
    for (auto &v : x) cin >> v;
    for (int k = 0; k < n; ++k) {
        if (n == 1) { cout << 0 << '\n'; continue; }
        long long answer = LLONG_MAX;
        // 先感染左邻居，两位传播者再分别向两端移动。
        if (k > 0) answer = min(answer, max(x[k] - x[0], x[n - 1] - x[k - 1]) / 2);
        // 对称地考虑先感染右邻居。
        if (k + 1 < n) answer = min(answer, max(x[k + 1] - x[0], x[n - 1] - x[k]) / 2);
        cout << answer << '\n';
    }
}
```

### 易错点

所有人都能移动，不能把人固定在初始位置。不要仅用到两端的距离除二；最初朝哪侧传播也有限制。邻居不存在时跳过该式，单人单独输出零。
