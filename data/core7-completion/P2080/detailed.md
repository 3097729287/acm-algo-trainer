## P2080 增进感情

原题：[P2080](https://www.luogu.com.cn/problem/P2080)

### 从问题到算法

两人能否走到一起取决于总好感，幸福程度取决于差的绝对值，因此把原来的两个维度变成“差值”和“总和”。固定差值时，总和越大永远越好，其它较小总和可以丢弃。

令 dp[d] 为选若干已处理事件后，差值 d 能达到的最大总和。初始只有差零、和零可达。对每个事件，从旧数组复制一份表示不选，再把旧状态加上本次差与和，更新新数组。使用两个版本可以同时处理正负差，避免原地扫描方向错误。

每个差绝对值最多二百，三十件事的总差范围只有六千。用偏移量把负差映射到数组下标，处理完后枚举满足 dp[d]>=v 的状态，取 |d| 最小；没有状态就输出 −1。

### 复杂度

时间 O(n²A)，空间 O(nA)，A 为单项差值的上界。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, v;
    cin >> n >> v;
    vector<pair<int, int>> events(n);
    int bound = 0;
    for (auto &[a, b] : events) {
        cin >> a >> b;
        bound += abs(a - b);
    }
    const int neg = INT_MIN / 4;
    vector<int> dp(2 * bound + 1, neg);
    dp[bound] = 0;
    for (auto [a, b] : events) {
        auto next = dp;
        int difference = a - b;
        for (int i = 0; i < (int)dp.size(); i++)
            if (dp[i] != neg && i + difference >= 0 && i + difference < (int)dp.size())
                next[i + difference] = max(next[i + difference], dp[i] + a + b);
        dp.swap(next);
    }
    int ans = INT_MAX;
    for (int i = 0; i < (int)dp.size(); i++)
        if (dp[i] >= v)
            ans = min(ans, abs(i - bound));
    cout << (ans == INT_MAX ? -1 : ans) << '\n';

    return 0;
}
```

### 实现提醒

好感可负；保留最大总和而非最小；转移使用旧数组，防止重复选事件。
