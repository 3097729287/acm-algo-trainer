## E. 小芳的睡眠排序

### 题意

[原题链接](https://ac.nowcoder.com/acm/contest/141882/E)

原排列中下标为 $i$、数值为 $p_i$ 的元素在第 $i$ 秒开始睡眠，在第 $i+kp_i$ 秒醒来。按醒来时刻输出，时刻相同则原下标较小者先输出。给出原排列 $p$ 和目标排列 $q$，求能产生 $q$ 的非负整数 $k$ 的数量，无穷多个时输出 <code>inf</code>。

每组 $1\le n\le2\times10^5$；所有测试的 $n$ 之和不超过 $2\times10^5$。

### 从零讲：vector 与逆排列的下标

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


若数组是一到 $n$ 的排列，每个值恰好出现一次，就可以用另一个数组记录它的位置。对 $(3,1,2)$ 执行 $\verb@pos[p[i]]=i@$ 后得到 $\mathrm{pos}[3]=1$、$\mathrm{pos}[1]=2$、$\mathrm{pos}[2]=3$。建立数组需要 $O(n)$ 时间，之后由数值查原位置为 $O(1)$。有重复值时，一个数只存一个下标会覆盖旧信息，不能直接套用。

$\verb@std::min(a,b)@$、$\verb@std::max(a,b)@$ 分别返回较小、较大的值；要维护逐渐收紧的范围，可写 $\verb@low=std::max(low,new_low);@$、$\verb@high=std::min(high,new_high);@$。它们只比较两个数，均为 $O(1)$，并不会自动保证最终范围非空。

</details>

### 思路

记录每个数在原排列中的位置 $\mathrm{pos}[v]$。数值 $v$ 的醒来时刻为

$$t_v=\mathrm{pos}[v]+kv.$$

目标顺序只需逐对检查相邻元素：若每一对都按“醒来时刻、原下标”递增，整个目标序列就正确。

![不同参数下的实际醒来时刻](assets/e-wake.svg)

设相邻目标为先 $u$、后 $v$，分两种数值关系求约束。

**当 $u<v$：** 若 $\mathrm{pos}[u]<\mathrm{pos}[v]$，它本来就早入睡、睡得也更短，所有非负 $k$ 都可。否则，平局会让 $v$ 先输出，必须严格满足

$$\mathrm{pos}[u]+ku<\mathrm{pos}[v]+kv,$$

即 $k(v-u)>\mathrm{pos}[u]-\mathrm{pos}[v]$。整数下界是

$$k\ge\left\lfloor\frac{\mathrm{pos}[u]-\mathrm{pos}[v]}{v-u}\right\rfloor+1.$$

**当 $u>v$：** 若 $\mathrm{pos}[u]>\mathrm{pos}[v]$，它入睡更晚且睡得更长，永远不能先输出，直接无解。否则允许同时醒来，因为 $u$ 的原下标较小，所以

$$k(u-v)\le\mathrm{pos}[v]-\mathrm{pos}[u],\qquad
k\le\left\lfloor\frac{\mathrm{pos}[v]-\mathrm{pos}[u]}{u-v}\right\rfloor.$$

把所有下界取最大、所有上界取最小，与 $k\ge0$ 相交。图中目标 $(2,1,3)$：第一对要求 $k\le2$，第二对要求 $k\ge1$，答案为二。

有限上界至多为 $n-1$，所有下界也至多为 $n$，所以代码以 $\verb@high=n;@$ 表示尚无上界。交集为空时输出零；没有上界时输出 <code>inf</code>；否则输出 $\mathrm{high}-\mathrm{low}+1$。当 $n=1$ 没有相邻约束，自然得到 <code>inf</code>。

时间复杂度 $O(n)$，额外空间 $O(n)$，不需要真的模拟睡眠或排序。

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
        vector<int> pos(n + 1), q(n);
        for (int i = 1; i <= n; ++i) {
            int v;
            cin >> v;
            pos[v] = i;
        }
        for (int i = 0; i < n; ++i) cin >> q[i];
        int low = 0, high = n;
        // 有限上界至多为 n-1，故用 n 表示尚无上界。
        for (int i = 0; i + 1 < n; ++i) {
            int u = q[i], v = q[i + 1];
            if (u < v) {
                if (pos[u] > pos[v]) {
                    // 原来较晚入睡的 u 必须严格早醒，平局会让 v 先输出。
                    low = max(low, (pos[u] - pos[v]) / (v - u) + 1);
                }
            } else {
                if (pos[u] > pos[v]) {
                    high = -1;
                } else {
                    // 原来较早入睡的 u 可以和 v 同时醒来。
                    high = min(high, (pos[v] - pos[u]) / (u - v));
                }
            }
        }
        if (low > high) cout << 0 << '\n';
        else if (high == n) cout << "inf\n";
        else cout << high - low + 1 << '\n';
    }
}
```

### 易错点

平局比较原下标；较晚入睡者要严格早醒，不能把所有条件都写成小于等于。先检查空交集，再判断 <code>inf</code>。
