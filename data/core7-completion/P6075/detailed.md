## P6075 子集选取

原题：[P6075](https://www.luogu.com.cn/problem/P6075)

### 从问题到算法

集合包含关系可以逐元素检查：某个元素若出现在右侧或下侧的子集中，就必须同时出现在它的前驱中。因此每个元素的出现位置构成从左上角扩张的阶梯区域。

在边长为 k 的三角格中，这样的阶梯区域与从 {1,…,k} 中选择若干互不相同的阶梯长度一一对应：依次取边界的严格下降长度即可恢复整个区域。每个长度可选或不选，所以一个元素有 2^k 种合法出现模式。k=2 时四种模式为全不出现、只在顶格出现、在前两格出现、全部出现。

不同元素是否出现在某个集合中互不干涉，选择好每个元素的合法模式即可确定全部子集。由乘法原理得到 (2^k)^n。代码先算 2^k，再对 n 快速幂，避免直接计算 n·k 时超出输入类型。

### 复杂度

时间 O(log n+log k)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

long long power(long long a, long long b, long long mod) {
    long long r = 1;
    for (; b; b >>= 1, a = a * a % mod)
        if (b & 1)
            r = r * a % mod;
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long n, k;
    cin >> n >> k;
    const long long mod = 1000000007;
    cout << power(power(2, k, mod), n, mod) << '\n';

    return 0;
}
```

### 实现提醒

空子集允许；元素彼此独立；模数为 1000000007。
