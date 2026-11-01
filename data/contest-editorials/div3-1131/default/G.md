## G. 0s and 1s

### 题意

[原题链接](https://codeforces.com/contest/2278/problem/G)

根为一的树，每点有初始二进制状态 $x_v$ 和目标 $y_v$。给根注入一个脉冲：零变一并停止，一变零并向所有孩子各发一脉冲。求达到全部目标的最少根脉冲数，模 $998244353$；不可达输出负一。$1\le n\le2\times10^5$，总 $n\le2\times10^5$。

### 从零讲：位运算：把非负整数看成一组二进制开关

<details>
<summary>展开可复用的基础知识</summary>

#### 位运算：把非负整数看成一组二进制开关

五写成二进制为 $0101_2$，三为 $0011_2$。同一列各代表一位：按位与 $\verb@&@$ 两边都为一才得一，按位或 $\verb@|@$ 任一为一就得一，按位异或 $\verb@^@$ 不同才为一。所以 $5\mathbin{\&}3=1$，$5\mathbin{|}3=7$，$5\mathbin{\oplus}3=6$。

![相同数值分别写成每一位，逐列计算与、或、异或](assets/foundation-bitwise-bits.svg)

$\verb@1ULL << k@$ 把一移到第 $k$ 位。对非负无符号整数，$\verb@(mask >> k) & 1ULL@$ 读该位，$\verb@mask | (1ULL<<k)@$ 置一，$\verb@mask & ~(1ULL<<k)@$ 清零，$\verb@mask ^ (1ULL<<k)@$ 翻转。最低位编号为零。

```cxx
unsigned long long mask = 5; // 第 0、2 位为一
bool has = (mask >> 2) & 1ULL; // true
mask |= 1ULL << 1;             // 变成 7
```

位移次数必须小于类型位宽，且不能为负；不要用普通 $\verb@1@$ 去移到超出 int 范围的位置。C++17 有符号负数右移和溢出的规则不适合直接套“乘除二的幂”，用明确范围的无符号数更容易保证行为。$\verb@^@$ 是异或，绝不是乘方。

逻辑与 $\verb@&&@$、逻辑或 $\verb@||@$ 将整体条件视为真假，并会短路；按位 $\verb@&@$、$\verb@|@$ 逐位计算，不会因此跳过右侧表达式。运算符优先级可能与直觉不同，写 $\verb@(mask & bit) != 0@$，别省掉关键括号。

固定机器字内的一次位运算按 $O(1)$ 估算；枚举全部 $k$ 位状态仍有 $2^k$ 种，不能因为每次运算快就忽略状态数。$\verb@x & (x-1)@$ 对正无符号数清掉最低的一位；GCC 的 $\verb@__builtin_popcountll(x)@$ 统计一的数量，注意实参位宽与具体编译器支持。


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

沿任意根路径，这个过程与二进制加法相同：根是最低位，遇零变一停止，遇一变零并产生进位。注入 $K$ 次，相当于给每条路径的初始二进制数加 $K$。

![根脉冲一次后停止，再一次触发向两个孩子的进位](assets/g-pulses.svg)

设深度 $d$ 对应 $K$ 的第 $d$ 位 $k_d$，当前路径进入点 $v$ 的加法进位为 $c_v$，根进位为零。目标要求
$$x_v\oplus k_d\oplus c_v=y_v,\qquad k_d=x_v\oplus y_v\oplus c_v.$$
同一深度必须共用同一位 $k_d$；要求不同则无解。给孩子的进位是 $\lfloor(x_v+k_d+c_v)/2\rfloor$，只可能为零或一。

![同层共用K的一位，但两条分支的加法进位可以不同](assets/g-carries.svg)

用显式 DFS 栈逐点检查并确定每一位。每一层至少有一个点，故从最低位到最深层的位全被强制确定；更高位不影响任意节点，全部置零便得到最小 $K$。答案累计 $k_d2^d$ 的模值即可，无须保存巨大整数。

时间、空间均为 $O(n)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
const long long MOD = 998244353;
struct State { int node, parent, depth, carry; };
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<vector<int>> graph(n);
        for (int i = 1, u, v; i < n; ++i) {
            cin >> u >> v; --u; --v;
            graph[u].push_back(v); graph[v].push_back(u);
        }
        string x, y;
        cin >> x >> y;
        vector<int> bit(n, -1);
        vector<long long> power(n, 1);
        for (int i = 1; i < n; ++i) power[i] = power[i - 1] * 2 % MOD;
        vector<State> stack = {{0, -1, 0, 0}};
        bool possible = true;
        long long answer = 0;
        while (!stack.empty()) {
            State current = stack.back(); stack.pop_back();
            int u = current.node, depth = current.depth;
            int xb = x[u] - '0', yb = y[u] - '0';
            int needed = xb ^ yb ^ current.carry;
            if (bit[depth] == -1) {
                bit[depth] = needed;
                answer = (answer + needed * power[depth]) % MOD;
            } else if (bit[depth] != needed) {
                possible = false; break;
            }
            // 同一深度共用 K 的这一位，但每条根路径的进位可以不同。
            int next_carry = (xb + needed + current.carry) / 2;
            for (int v : graph[u]) if (v != current.parent)
                stack.push_back({v, u, depth + 1, next_carry});
        }
        cout << (possible ? answer : -1) << '\n';
    }
}
```

### 易错点

根是最低位。同一深度共享 K 的位，不共享路径进位。先判断可达与最小二进制位，再对答案取模；不能对脉冲次数取模后模拟。
