## P11894 Update

原题：[P11894](https://www.luogu.com.cn/problem/P11894)

### 从问题到算法

所有操作都独立地把一个数替换为同一个函数 f(x)，所以作用在某个位置上的先后顺序没有区别，只需知道总次数。区间覆盖次数通过差分数组在 O(n+m) 时间求出。

对当前值 x>1，令 b=floor(log2 x)，在到达 2^(b+1) 前，每次都增加 b。距离下个分界还差 gap=2^(b+1)−x，需要 ceil(gap/b) 步才首次到达或越过分界。这些步的起始值仍在当前分段，增量都为 b，可以一次完成。

跳过的步数还要与剩余次数取最小值。越过分界后重新计算 b，直到次数用完。x=1 时增量为零，永远不变。用整数最高位运算代替浮点 log，避免二次幂附近误差。

### 复杂度

时间 O(n log A+m)，空间 O(n)，A 为操作后的最大值。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<long long> a(n + 1);
    vector<int> difference(n + 2);
    for (int i = 1; i <= n; i++)
        cin >> a[i];
    while (m--) {
        int l, r;
        cin >> l >> r;
        difference[l]++;
        difference[r + 1]--;
    }
    int count = 0;
    for (int i = 1; i <= n; i++) {
        count += difference[i];
        long long left = count, x = a[i];
        while (left && x > 1) {
            int b = 63 - __builtin_clzll(x);
            long long gap = (1LL << (b + 1)) - x, steps = min(left, (gap + b - 1) / b);
            x += steps * b;
            left -= steps;
        }
        cout << x << (i == n ? '\n' : ' ');
    }

    return 0;
}
```

### 实现提醒

x=1 不动；跳跃次数向上取整；更新后的最高位重新计算。
