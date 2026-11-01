## B. Stakes and Shapes

### 题意

[原题链接](https://codeforces.com/contest/2278/problem/B)

Alice 在 $x+y+z$ 局中分别出 $x$ 次石头、$y$ 次剪刀、$z$ 次布，顺序未知。Bob 须提前确定全部手势，保证对方任意排列下，自己赢局数不少于输局数。输出任意满足条件的字符串。$0\le x,y,z\le100$，总局数为正。

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

找出 Alice 出现最多的手势，Bob 每局都出克制它的手势。例如剪刀最多，就全部出石头：赢 $y$ 局、输 $z$ 局，因为 $y\ge z$，所以不会输多赢少。

Bob 每局都出同一种手势，计分只取决于三类手势各有多少次，与 Alice 的排列顺序无关。出现最多的类别并列时任选一个即可。时间与输出长度相同，为 $O(x+y+z)$；构造输出字符串的空间也为 $O(x+y+z)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int x, y, z;
        cin >> x >> y >> z;
        char move;
        // 始终克制 Alice 出现最多的手势，赢局数便不会小于输局数。
        if (x >= y && x >= z) move = 'P';
        else if (y >= z) move = 'R';
        else move = 'S';
        cout << string(x + y + z, move) << '\n';
    }
}
```

### 易错点

手势字符对应 R 石头、S 剪刀、P 布；要输出最大频次类别的克制手势。答案不唯一，不能逐字与样例比较。
