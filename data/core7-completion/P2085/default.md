## P2085 最小函数值

原题：[P2085](https://www.luogu.com.cn/problem/P2085)

### 思路

每个二次函数在正整数 x 上给出一个递增序列。先把各函数的 f(1) 入堆，弹出最小值后输出，并把同一函数的下一个 x 对应值放回。

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
