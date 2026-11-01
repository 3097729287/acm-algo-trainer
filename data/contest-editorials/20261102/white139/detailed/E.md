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

#### 先把“原下标”和“目标顺序”分开

入睡时间取决于原排列位置，不能用目标排列中的位置计算。先建立 $\mathrm{pos}[v]$，表示数值 $v$ 在原排列中的下标。随后它的醒来时刻是

$$t_v=\mathrm{pos}[v]+kv.$$

完整比较顺序是二元组 $(t_v,\mathrm{pos}[v])$：先比较醒来时刻，再比较原下标。原排列是排列，因此原下标也各不相同，任意两个元素都有确定的先后顺序。

#### 用一个例子同时看上界、下界和平局

取原排列 $p=(2,3,1)$、目标 $q=(2,1,3)$。原位置为 $\mathrm{pos}[2]=1$、$\mathrm{pos}[3]=2$、$\mathrm{pos}[1]=3$。

![参数变化时各数值真正醒来的时刻](assets/e-wake.svg)

第一对目标是先二后一。二的原位置较小，可以同时醒来，所以要求

$$1+2k\le3+k\quad\Longleftrightarrow\quad k\le2.$$

第二对目标是先一后三。一的原位置更大，同时醒来时三会先输出，因此必须严格早醒：

$$3+k<2+3k\quad\Longleftrightarrow\quad1<2k\quad\Longleftrightarrow\quad k\ge1.$$

合起来是 $1\le k\le2$，恰好两个整数。图中 $k=2$ 时二和一同时在第五秒醒来，原下标一的二先输出，所以端点二必须计入。

#### 为什么检查相邻元素就足够

把目标写成 $q_1,q_2,\ldots,q_n$。若每对相邻元素对应的二元组都递增，那么由比较关系的传递性，任意更早目标位置的二元组都小于更后位置，目标排列就是整体排序结果。

反过来，只要某对相邻元素比较顺序反了，实际输出就不可能等于目标。因此这 $n-1$ 个约束既必要也充分，不需要检查全部元素对。

#### 相邻数值递增时，只可能给下界

设相邻目标先 $u$ 后 $v$，且 $u<v$。数值较小的 $u$ 睡眠时长增加得更慢。

如果 $\mathrm{pos}[u]<\mathrm{pos}[v]$，则它入睡更早，睡得也更短，对每个非负 $k$ 都先醒，无须增加约束。

如果 $\mathrm{pos}[u]>\mathrm{pos}[v]$，平局会把顺序排成先 $v$ 后 $u$，必须严格满足

$$\mathrm{pos}[u]+ku<\mathrm{pos}[v]+kv.$$

移项时，将较小数值对应的项放到右侧得到

$$k(v-u)>\mathrm{pos}[u]-\mathrm{pos}[v].$$

右边为正，除数 $v-u$ 也为正。非负整数除法给出的商是向下取整，而这里要求严格大于，所以最小整数是

$$\left\lfloor\frac{\mathrm{pos}[u]-\mathrm{pos}[v]}{v-u}\right\rfloor+1.$$

尤其当分子恰好整除分母时，也必须再加一，否则会错误允许平局。程序用这项收紧 <code>low</code>。

#### 相邻数值递减时，只可能给上界或无解

现在 $u>v$。如果 $\mathrm{pos}[u]>\mathrm{pos}[v]$，$u$ 同时具有“更晚入睡”和“睡得更久”两个劣势，对 $k\ge0$ 都无法先输出，直接把区间标记为空。

否则 $\mathrm{pos}[u]<\mathrm{pos}[v]$，允许平局，因此要求

$$\mathrm{pos}[u]+ku\le\mathrm{pos}[v]+kv,$$

即

$$k(u-v)\le\mathrm{pos}[v]-\mathrm{pos}[u].$$

两侧差值均为正，最大合法整数为

$$\left\lfloor\frac{\mathrm{pos}[v]-\mathrm{pos}[u]}{u-v}\right\rfloor.$$

这次是小于等于，恰好整除时商本身合法，不能减一。程序用它收紧 <code>high</code>。

#### 交集为什么仍然只是一个区间

每对相邻元素只给出一个整数下界、一个整数上界或无解。所有要求同时满足，等价于取最大下界、最小上界，并加入 $k\ge0$。

所有有限上界都不超过 $n-1$：分子至多为 $n-1$，分母至少为一。下界也至多为 $n$。所以可以初始化 $\verb@low=0, high=n;@$，其中 $\verb@high==n@$ 专门表示从未得到有限上界。

先检查 $\verb@if (low > high)@$，此时没有合法参数，输出零。若交集非空而 $\verb@high==n@$，参数只受下界限制，输出 <code>inf</code>；否则从下界到上界逐个计数，数量为 $\mathrm{high}-\mathrm{low}+1$。必须先检查空集，避免将已经无解的情况误判成无穷。

例如 $p=(4,2,1,3)$、$q=(2,1,4,3)$，第一对给 $k\le1$，第二对给 $k\ge1$，第三对给 $k\le3$，交集仅含一。$n=1$ 时没有相邻对，也就没有上界，答案为 <code>inf</code>。

记录位置、读取目标、扫描相邻对均为线性时间，时间复杂度 $O(n)$，额外空间 $O(n)$。计算的都是位置差与数值差，参考程序无需实际计算可能很大的醒来时刻。

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
