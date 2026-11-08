## AT_dp_j Sushi

原题：[AT_dp_j](https://www.luogu.com.cn/problem/AT_dp_j)

### 思路

状态只记录分别剩一、二、三个寿司的盘数 a,b,c。选到空盘会原地停留，把这部分期望移到等式左边，得到 E=(n+aE1+bE2+cE3)/(a+b+c)。

### 复杂度

时间 O(n³)，空间 O(n³)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    int count[4] = {};
    for (int i = 0; i < n; i++) {
        int x;
        cin >> x;
        count[x]++;
    }
    int side = n + 2;
    vector<double> dp((size_t)side * side * side);
    auto at = [&](int a, int b, int c) -> double & {
        return dp[((size_t)c * side + b) * side + a];
    };
    for (int c = 0; c <= n; c++)
        for (int b = 0; b + c <= n; b++)
            for (int a = 0; a + b + c <= n; a++) {
                if (a + b + c == 0)
                    continue;
                double value = n;
                if (a)
                    value += a * at(a - 1, b, c);
                if (b)
                    value += b * at(a + 1, b - 1, c);
                if (c)
                    value += c * at(a, b + 1, c - 1);
                at(a, b, c) = value / (a + b + c);
            }
    cout << fixed << setprecision(12) << at(count[1], count[2], count[3]) << '\n';

    return 0;
}
```

### 实现提醒

分子常数是总盘数 n；分母是非空盘数；不能忽略选到空盘的操作。
