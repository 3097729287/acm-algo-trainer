## P2085 最小函数值

原题：[P2085](https://www.luogu.com.cn/problem/P2085)

### 从问题到算法

题目系数保证函数在正整数范围递增，因此每个函数尚未输出的最小值一定是它当前的首项。把每条序列的首项放进小根堆，全局最小值就是堆顶。

弹出时同时保存函数编号与当前 x，输出该值后，仅这条序列向前一步，计算 f(x+1) 再入堆。其余函数的候选不变。

不同函数或不同 x 可能给出相同数值，它们仍属于多个函数值，必须按出现次数分别输出，不能去重。计算二次项先转六十四位。

### 复杂度

时间 O((n+m) log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<array<long long, 3>> f(n);
    for (auto &v : f)
        cin >> v[0] >> v[1] >> v[2];
    auto value = [&](int i, long long x) { return f[i][0] * x * x + f[i][1] * x + f[i][2]; };
    using Item = tuple<long long, int, int>;
    priority_queue<Item, vector<Item>, greater<Item>> q;
    for (int i = 0; i < n; i++)
        q.push({value(i, 1), i, 1});
    for (int step = 0; step < m; step++) {
        auto [v, i, x] = q.top();
        q.pop();
        cout << v << (step + 1 == m ? '\n' : ' ');
        q.push({value(i, x + 1), i, x + 1});
    }

    return 0;
}
```

### 实现提醒

依赖函数单调；重复值保留；堆中保存函数身份和 x。
