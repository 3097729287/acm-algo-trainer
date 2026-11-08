## P1858 多人背包

原题：[P1858](https://www.luogu.com.cn/problem/P1858)

### 从问题到算法

把方案按是否包含当前物品分成两类。两类清单互不相同，内部仍按价值降序，故可以线性归并出整体前 K 项。只保留前 K 不会丢失未来最优：同一容量的较差旧方案，后续加相同物品集合仍不会超过已保留的 K 个方案。

容量必须倒序，确保每种物品只取一次。初始只有容量零有一个价值零的空方案，其它容量没有方案，不能用零冒充可达状态。价值相等时仍保留两项，因为题目区分物品清单。

原题没有定义“凑满容量的不同清单少于 K 个”时应输出什么。本实现对题目目标可行的输入求完整最优和；不足 K 时不臆造零价值方案或约定答案，相关题面边界单独保留在验证记录中。

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
