## P12733 磨合

原题：[P12733](https://www.luogu.com.cn/problem/P12733)

### 思路

要做 k 题应选择难度最小的 k 题，并按难度从大到小处理。将难度升序排列后，最小耗时满足 cost[k]=cost[k−1]+前 k 题难度和，预处理后每次二分数量。

### 复杂度

时间 O(n log n+q log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<long long> d(n), cost(n + 1);
    for (auto &x : d)
        cin >> x;
    sort(d.begin(), d.end());
    long long sum = 0;
    for (int i = 1; i <= n; i++) {
        sum += d[i - 1];
        cost[i] = cost[i - 1] + sum;
    }
    while (q--) {
        long long t;
        cin >> t;
        cout << upper_bound(cost.begin(), cost.end(), t) - cost.begin() - 1 << '\n';
    }

    return 0;
}
```

### 实现提醒

排序后是从大到小执行；预处理用升序前缀和；t=0 返回 0。
