## P12733 磨合

原题：[P12733](https://www.luogu.com.cn/problem/P12733)

### 从问题到算法

处理位置的时间系数为 1、2、…、k。若较大的难度被放到较大的系数上，交换它与更小难度就能减少或保持耗时，因此最优顺序是难度降序。同时所有系数为正，把选中的题替换成更简单的未选题不会变差，所以只选最小的 k 题。

设升序难度为 d1…dn。增加第 k 道题时，新选的 dk 是当前最大，应放在第一位；原来的 k−1 道题系数全部加一，增加耗时为 dk+Σ前k−1难度，即前 k 项和。由此一次扫描预处理全部 cost。

cost 随数量严格递增，每次询问用 upper_bound 找最后一个不超过 t 的代价，返回对应题数。总耗时可达十的十五次方，使用 long long。

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
