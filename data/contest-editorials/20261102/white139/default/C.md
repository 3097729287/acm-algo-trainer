## C. 小芳的比赛

### 题意

[原题链接](https://ac.nowcoder.com/acm/contest/141882/C)

原本每轮小芳获胜。改判第 $i$ 轮让小苯获胜需要代价 $c_i>0$。设两人的分差为“小芳得分减小苯得分”，要求每个前缀的分差不超过 $x$，最终分差严格大于零。求最小代价，无解输出 $-1$。

每组 $1\le x\le n\le2\times10^5$、$c_i\le10^9$；所有测试的 $n$ 之和不超过 $2\times10^5$。过程中允许小芳落后，题目没有规定分差下限。

### 从零讲：小根堆与 priority_queue

<details>
<summary>展开基础知识</summary>

优先队列用来反复取当前集合中的最小值或最大值，不要求取出后还能按插入顺序遍历。C++ 的 $\verb@priority_queue@$ 默认取最大值；下面的第三个模板参数将它改为小根堆：

```cxx
priority_queue<long long, vector<long long>, greater<long long>> h;
h.push(8);
h.push(3);
h.push(10);
long long cheapest = h.top(); // 返回 3，堆仍有三项
h.pop();                     // 删除 3，不返回数值
```

第一个参数是元素类型，第二个参数 $\verb@std::vector<long long>@$ 是底层数组，$\verb@std::greater<long long>@$ 规定较小值优先。使用 queue、vector、functional；参考程序的 $\verb@<bits/stdc++.h>@$ 是 GCC 提供的汇总头文件。

堆在完全二叉树中维护“父节点不大于孩子”。新值放到末尾后沿父节点上移；删除堆顶时将末尾放到根，再沿较小的孩子下移。树高为 $O(\log m)$，所以有 $m$ 个元素时，$\verb@push@$、<code>pop</code> 为 $O(\log m)$，<code>top</code> 为 $O(1)$，空间为 $O(m)$。底层数组整体并没有排好序。

只有非空堆才能调用 <code>top</code>、<code>pop</code>；可用 <code>empty()</code> 判断。相同的代价值可以存多次，弹出一次只删除一个元素。堆适合不断加入候选、反复取最小值，不支持直接定位并删除任意中间元素。

</details>

### 从零讲：整数类型与累加范围

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

如果前 $i$ 轮改判了 $t$ 轮，小芳得 $i-t$ 分，小苯得 $t$ 分，分差就是 $i-2t$。因此扫描到第 $i$ 轮时，只要 $i-2t>x$，就必须从前 $i$ 轮中再选一轮改判。

![前缀分差与改判位置](assets/c-prefix.svg)

把已扫描、尚未改判的所有代价放入小根堆。每轮先加入 $c_i$；若当前分差超限，就取出堆中最小代价，累加并让改判次数增加一。堆里可能弹出以前某轮的代价：扫描只是在规划最终改判集合，选择较早轮次会降低之后的分差，不会破坏已满足的上限。

每次只需补一轮，因为上一轮的分差已经不超过 $x$，本轮原本获胜只会使它增加一，而一次改判会使它降低二。

为什么取最便宜的正确？在某次必须补选的时刻 $i$，设之前已选集合为 $G$。任意包含 $G$ 的最优方案都还必须在前 $i$ 轮里选一个未选轮次 $h$。用堆顶 $g$ 代替它，代价不会增加：时刻 $i$ 之前的要求已由 $G$ 保证；时刻 $i$ 及之后的前缀同时包含 $g,h$，替换不改变改判总数。逐次交换，就能得到包含所有贪心选择的最优方案。

最终若改判次数为 $t$，还要检查 $n-2t>0$。贪心只在前缀强制要求时增加次数，已是满足所有前缀的最少次数；如果这样仍不能获胜，增加改判只会更差，输出 $-1$。

时间复杂度 $O(n\log n)$，额外空间 $O(n)$。总代价需要 $\verb@long long@$。

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
        int n, x;
        cin >> n >> x;
        priority_queue<long long, vector<long long>, greater<long long>> heap;
        long long ans = 0;
        int changed = 0;
        for (int i = 1; i <= n; ++i) {
            long long c;
            cin >> c;
            heap.push(c);
            if (i - 2 * changed > x) {
                // 当前前缀必须再改一场，选尚未改判的最小代价。
                ans += heap.top();
                heap.pop();
                ++changed;
            }
        }
        // 改判只会降低小芳的分差，最少次数仍不能赢就无解。
        cout << (n - 2 * changed > 0 ? ans : -1) << '\n';
    }
}
```

### 易错点

堆中保留过去尚未选中的轮次；一次改判使分差减少二。允许过程中分差为负，最终却必须严格为正。无解时也要读完当前组输入。
