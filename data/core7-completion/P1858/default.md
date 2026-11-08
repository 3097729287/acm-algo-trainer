## P1858 多人背包

原题：[P1858](https://www.luogu.com.cn/problem/P1858)

### 思路

每个容量维护前 K 大方案价值，归并不取与取当前物品的两份有序列表。相同价值、不同清单分别保留。这里求至少存在 K 种装满方案时的最优和；不足 K 种的输出原题未规定，详细题解明确标注。

### 复杂度

时间 O(NVK)，空间 O(VK)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int K, V, N;
    cin >> K >> V >> N;
    vector<vector<long long>> dp(V + 1);
    dp[0] = {0};
    for (int i = 0; i < N; i++) {
        int w;
        long long value;
        cin >> w >> value;
        for (int capacity = V; capacity >= w; capacity--) {
            const auto &left = dp[capacity];
            const auto &right = dp[capacity - w];
            vector<long long> next;
            int a = 0, b = 0;
            while ((int)next.size() < K && (a < (int)left.size() || b < (int)right.size())) {
                if (b == (int)right.size() || (a < (int)left.size() && left[a] >= right[b] + value))
                    next.push_back(left[a++]);
                else
                    next.push_back(right[b++] + value);
            }
            dp[capacity].swap(next);
        }
    }
    if ((int)dp[V].size() < K)
        return 0;
    cout << accumulate(dp[V].begin(), dp[V].end(), 0LL) << '\n';

    return 0;
}
```

### 实现提醒

恰好装满；容量倒序；等值不同清单不去重；不存在的方案不用零填充。
