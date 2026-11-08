## P2789 直线交点数

原题：[P2789](https://www.luogu.com.cn/problem/P2789)

### 思路

没有三线共点时，每对不平行直线产生唯一交点。将直线按斜率分组，添加 k 条新平行线到已有 i 条线时增加 ik 个交点。布尔 DP 记录每种线数可达到的交点数。

### 复杂度

时间 O(n⁴)，空间 O(n³)，n<=25。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    int maximum = n * (n - 1) / 2;
    vector<vector<char>> dp(n + 1, vector<char>(maximum + 1));
    dp[0][0] = 1;
    for (int i = 0; i < n; i++)
        for (int s = 0; s <= maximum; s++)
            if (dp[i][s])
                for (int k = 1; i + k <= n; k++)
                    dp[i + k][s + i * k] = 1;
    cout << count(dp[n].begin(), dp[n].end(), 1) << '\n';

    return 0;
}
```

### 实现提醒

只问不同交点数量有几种；新组内部平行；不能把三线共点计为一种压缩方式。
