## B. 奶龙的奇妙公式

### 题意

[原题链接](https://ac.nowcoder.com/acm/contest/141882/B)

给定正整数数组，计算

$$\sum_{i=1}^{n}\sum_{j=i}^{n}\left(\min(a_i,a_j)+\max(0,a_j-a_i)\right).$$

每组 $1\le n\le2\times10^5$、$1\le a_i\le10^6$；所有测试的 $n$ 之和不超过 $2\times10^5$。

### 从零讲：整数类型与乘法的计算顺序

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

固定一对 $i\le j$，按大小分两种情况：

- 若 $a_j\ge a_i$，原项为 $a_i+(a_j-a_i)=a_j$。
- 若 $a_j<a_i$，原项为 $a_j+0=a_j$。

所以每一项都只贡献 $a_j$。固定右端点 $j$ 后，左端点 $i$ 有 $1,2,\ldots,j$ 共 $j$ 种选择，答案为

$$\boxed{\sum_{j=1}^{n}j\,a_j}.$$

例如 $(2,5,1)$ 的贡献依次为 $2$、$2\times5$、$3\times1$，合计十五。读入第 $j$ 个数时直接累加即可，无须保存数组。

时间复杂度 $O(n)$，额外空间 $O(1)$。答案最多为 $10^6n(n+1)/2$，需要 $\verb@long long@$。

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
        long long ans = 0;
        for (int j = 1; j <= n; ++j) {
            long long a;
            cin >> a;
            // 原式中每一项都等于 a_j，它对应 j 个左端点。
            ans += j * a;
        }
        cout << ans << '\n';
    }
}
```

### 易错点

系数是从一开始的右端点 $j$；$i=j$ 的项也包含在内。乘法和答案都要在 $\verb@long long@$ 范围内计算。
