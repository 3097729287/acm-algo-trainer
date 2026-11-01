## F. 小月的川菜

### 题意

[原题链接](https://ac.nowcoder.com/acm/contest/142559/F)

将辣度 $1,\ldots,n$ 的菜一一分给 $n$ 位朋友。朋友 $i$ 收到辣度大于 $a_i$ 的菜就喝一杯奶。求恰好两人喝奶的分配数，模 $10^9+7$。$2\le n\le400$，$0\le a_i\le n$，所有测试的 $n$ 之和不超过四百。

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

先计数“挑出若干位朋友，并保证他们不喝奶”的部分配对。令 $R_j$ 为挑出 $j$ 位朋友、给他们分配不同安全菜的方案数。把阈值排序后，处理当前阈值 $a$ 时，原先 $j-1$ 道已选安全菜都不超过 $a$，故新增配对有 $a-j+1$ 种。

![安全菜集合按阈值嵌套，已用的安全菜全部位于当前集合](assets/rook.svg)

不选择当前朋友，原 $R_j$ 保留；选择则增加 $R_{j-1}(a-j+1)$，系数为负时视为零。倒序更新 $j$。

记 $S_2=2R_{n-2}$、$S_1=R_{n-1}$、$S_0=R_n$，含义分别为留出二、一、零位朋友任意分配。对于实际有 $b$ 人喝奶的一份完整分配，三项的计数次数如下：

| 实际喝奶人数 | $S_2$ | $S_1$ | $S_0$ |
|---|---|---|---|
| 零 | $\binom n2$ | $n$ | 一 |
| 一 | $n-1$ | 一 | 零 |
| 二 | 一 | 零 | 零 |
| 多于二 | 零 | 零 | 零 |

所以答案是
$$S_2-(n-1)S_1+\binom n2 S_0=2R_{n-2}-(n-1)R_{n-1}+\binom n2R_n.$$
代入每一行可见：只保留实际恰好两人喝奶的方案，各一次。时间 $O(n^2)$，空间 $O(n)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
const long long MOD = 1000000007;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int T;
    cin >> T;
    while (T--) {
        int n;
        cin >> n;
        vector<int> a(n);
        for (int &x : a) cin >> x;
        sort(a.begin(), a.end());
        vector<long long> rook(n + 1);
        rook[0] = 1;
        for (int i = 0; i < n; ++i) {
            // 倒序保证 rook[j-1] 仍属于处理当前朋友之前。
            for (int j = i + 1; j >= 1; --j) {
                long long choices = max(0, a[i] - j + 1);
                rook[j] = (rook[j] + rook[j - 1] * choices) % MOD;
            }
        }
        long long pairs = 1LL * n * (n - 1) / 2 % MOD;
        long long ans = (2 * rook[n - 2] - (n - 1) * rook[n - 1] + pairs * rook[n]) % MOD;
        cout << (ans + MOD) % MOD << '\n';
    }
}
```

### 易错点

安全条件是菜编号小于等于阈值。重复阈值的朋友仍互相区分。滚动数组必须倒序更新；$n=2$ 时要正确保留 $R_0=1$。
