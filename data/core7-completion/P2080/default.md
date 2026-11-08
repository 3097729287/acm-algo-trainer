## P2080 增进感情

原题：[P2080](https://www.luogu.com.cn/problem/P2080)

### 思路

每件事贡献差值 a−b 和总值 a+b。用 0/1 背包维护每个差值下能得到的最大总值，最后在总值达到 v 的状态中取差值绝对值最小者。

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
