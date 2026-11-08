## P4799 世界冰球锦标赛 (Day2)

原题：[P4799](https://www.luogu.com.cn/problem/P4799)

### 思路

分别枚举两半装备的价格和并保留不超过预算的值。排序右半，对每个左半价格 x，用 upper_bound 统计右半中不超过 M−x 的个数。

### 复杂度

时间 O(n·2^(n/2))，空间 O(2^(n/2))。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long m;
    cin >> n >> m;
    vector<long long> a(n);
    for (auto &x : a)
        cin >> x;
    auto generate = [&](int l, int r) {
        vector<long long> s = {0};
        for (int i = l; i < r; i++) {
            int size = s.size();
            for (int j = 0; j < size; j++)
                if (a[i] <= m - s[j])
                    s.push_back(s[j] + a[i]);
        }
        return s;
    };
    auto l = generate(0, n / 2), r = generate(n / 2, n);
    sort(r.begin(), r.end());
    long long ans = 0;
    for (long long x : l)
        ans += upper_bound(r.begin(), r.end(), m - x) - r.begin();
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

相同价格的不同子集不能去重；答案和预算都用 long long。
