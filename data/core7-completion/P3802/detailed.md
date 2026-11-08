## P3802 小魔女帕琪

原题：[P3802](https://www.luogu.com.cn/problem/P3802)

### 从问题到算法

把全部晶体随机排列，每一步从剩余晶体中等概率选一个，等价于读取这个随机排列。对任意固定的七个连续位置，七种属性各出现一次的概率相同。

固定一种属性排列，概率为 ∏a_i 除以 S(S−1)…(S−6)，因为每种属性只取一次；七种属性有 7! 种顺序。令每个窗口的指示变量表示是否触发，其期望就是这个概率。即使窗口互相重叠，期望仍可直接相加，不要求事件独立。

窗口总数为 S−6，因此乘上这个数。S<7 时没有窗口，答案为零。使用 long double 逐项乘除，避免先计算巨大整数乘积。

### 复杂度

时间 O(1)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long a[7], sum = 0;
    for (auto &x : a) {
        cin >> x;
        sum += x;
    }
    long double ans = 0;
    if (sum >= 7) {
        ans = 5040.0L * (sum - 6);
        for (int i = 0; i < 7; i++)
            ans = ans * a[i] / (sum - i);
    }
    cout << fixed << setprecision(3) << ans << '\n';

    return 0;
}
```

### 实现提醒

重叠窗口都计数；不足七个时为零；某属性数量为零时概率自然为零。
