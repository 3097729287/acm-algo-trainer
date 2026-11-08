## P2789 直线交点数

原题：[P2789](https://www.luogu.com.cn/problem/P2789)

### 从问题到算法

交点数量只受哪些线平行影响。不同平行类中的任意两线相交，且没有三线共点保证这些交点各不相同；同类内不相交。

设 dp[i][s] 表示 i 条直线可以得到 s 个交点。再加入一组 k 条相互平行、且与已有所有线均不平行的新线，它们内部不产生交点，与原图增加 i·k 个交点，所以更新 dp[i+k][s+i·k]。

每一种平行类划分都能按某个组序生成，所有生成结果也都能选择不同斜率实现；不必统计生成次数，只记录是否可达，重复划分不会影响答案。n<=25，最大交点数为 C(n,2)，直接枚举状态和新组大小即可。

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
