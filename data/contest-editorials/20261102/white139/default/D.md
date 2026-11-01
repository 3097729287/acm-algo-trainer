## D. 小苯的纸牌屋

### 题意

[原题链接](https://ac.nowcoder.com/acm/contest/141882/D)

选择数组中的一个非空连续区间，使用其中所有纸牌搭成题图规定的正整数层纸牌屋。每条边都要一张纸牌，不能浪费。求合法区间的最大权值和。

每组 $3\le n\le2\times10^5$、$-10^9\le a_i\le10^9$；所有测试的 $n$ 之和不超过 $2\times10^5$。

### 从零讲：vector、下标与初始极小值

<details>
<summary>展开基础知识</summary>

$\verb@std::vector<T>@$ 是连续存放同一种类型元素的动态数组，需要 vector。$\verb@std::vector<int> a(n,0);@$ 建立恰好 $n$ 个零，合法下标为 $0$ 到 $n-1$；$\verb@vector<int> pos(n+1)@$ 则可使用下标 $n$。建数组需要 $O(n)$ 时间与空间，按下标访问为 $O(1)$。

```cxx
vector<int> a(3, 0);
a[1] = 7;                  // 现在是 0,7,0
a.push_back(9);             // 尾部追加，现在有四项
int last = a.back();        // 返回最后一项 9，不删除
a.pop_back();              // 删除最后一项，不返回它
```

$\verb@size()@$ 返回当前元素数量；$\verb@push_back@$ 均摊为 $O(1)$，扩容时会搬运已有元素，所以单次可能为 $O(n)$。$\verb@pop_back@$ 为 $O(1)$，空数组不能调用 <code>back</code> 或 $\verb@pop_back@$，也不能访问 $\verb@a[0]@$。$\verb@operator[]@$ 不负责检查越界。

扩容会使原来的迭代器、指针和引用失效；需要长期引用某一元素时，要确认之后不会扩容。$\verb@size()@$ 的返回类型是无符号整数，避免空数组上写 $\verb@size()-1@$。$\verb@static_cast<int>(a.size())@$ 是显式转成整数，应先保证数量没有超过 $\verb@int@$ 的表示范围。


取所有候选的最大值时，初始答案必须不大于任何合法结果。$\verb@numeric_limits<long long>::lowest()@$ 返回该整数类型能表示的最小值，需要 limits。它比直接写零适合处理所有候选均为负数的情况。

$\verb@std::max(a,b)@$ 返回两个同类型值中较大的一个，不会自动改写参数；所以更新最大值写成 $\verb@ans=std::max(ans,candidate);@$。$\verb@int length = static_cast<int>(len);@$ 在本题已经检查 $\mathrm{len}\le n\le2\times10^5$ 后才使用，转换不会丢失数值。

</details>

### 从零讲：整数乘法与负数

<details>
<summary>展开基础知识</summary>

整数类型决定能表示的范围。常见竞赛环境的 $\verb@int@$ 上界为 $2^{31}-1$，约为 $2.1\times10^9$；$\verb@long long@$ 的上界至少为 $2^{63}-1$，约为 $9.22\times10^{18}$。累加很多大数、求较长区间和时，应先估算结果，再选择类型。

```cxx
int a = 100000, b = 100000;
long long value = 1LL * a * b;
```

<code>1LL</code> 是 $\verb@long long@$ 常量，使右侧从第一次乘法起就在较宽的类型中计算。只把接收变量写成 $\verb@long long@$，不能修复右侧已发生的 $\verb@int@$ 溢出。若一个乘数本身已是 $\verb@long long@$，也会先将另一个乘数提升类型。

非负整数的除法向下取整，例如 <code>7/3</code> 得到二。负整数除法向零截断，因此不能直接当作数学上的向下取整。除数不得为零。选用较宽类型不会改变循环次数，时间复杂度仍按算法本身计算。

</details>

### 思路

先数合法长度。图中第 $r$ 层新增 $r$ 条左斜边、$r$ 条右斜边和 $r$ 条横边，共 $3r$ 张；底部横边也要计入。

![按层统计纸牌屋的边](assets/d-house.svg)

$k$ 层一共需要

$$L_k=3(1+2+\cdots+k)=\frac{3k(k+1)}2.$$

只枚举 $L_k\le n$ 的层数。合法长度依次为 $3,9,18,30,\ldots$，最多只有 $O(\sqrt n)$ 种。

固定合法长度 $L$，枚举右端点 $r=L,L+1,\ldots,n$。设 $S[r]$ 为前 $r$ 项的和，$S[0]=0$，则该区间的和为

$$S[r]-S[r-L].$$

![前缀相减留下长度九的区间](assets/d-prefix.svg)

图中 $S[10]$ 包含前十项，减去其中的第一项 $S[1]$，留下第 $2$ 到第 $10$ 项，权值和为十九。每个合法区间都有唯一的长度和右端点，所以这样恰好枚举全部候选。

时间复杂度 $O(n\sqrt n)$，额外空间 $O(n)$。由于 $n\ge3$，长度三一定存在；答案初始化为 $\verb@long long@$ 的最小值，不能初始化成零。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int T;
    cin >> T;
    while (T--) {
        int n;
        cin >> n;
        vector<long long> s(n + 1, 0);
        for (int i = 1; i <= n; ++i) {
            long long a;
            cin >> a;
            s[i] = s[i - 1] + a;
        }
        long long ans = numeric_limits<long long>::lowest();
        for (int k = 1; ; ++k) {
            long long len = 3LL * k * (k + 1) / 2;
            if (len > n) break;
            // 固定合法长度，再枚举右端点；非空区间也可能全为负。
            for (int r = static_cast<int>(len); r <= n; ++r) {
                ans = max(ans, s[r] - s[r - len]);
            }
        }
        cout << ans << '\n';
    }
}
```

### 易错点

按题图计入底部横边，最小合法长度是三；不能套用不含底边的纸牌屋公式。区间非空，答案可能为负。
