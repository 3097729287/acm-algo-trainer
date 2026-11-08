## CF888E Maximum Subsequence

原题：[CF888E](https://www.luogu.com.cn/problem/CF888E)

### 思路

把数组分成两半，分别枚举子集和对 m 的余数。对于左半余数 x，在排好序的右半余数中找不超过 m−1−x 的最大值，更新不回绕的最优和。

### 复杂度

时间 O(2^(n/2)·n)，空间 O(2^(n/2))。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long mod;
    cin >> n >> mod;
    vector<long long> a(n);
    for (auto &x : a)
        cin >> x;
    auto enumerate = [&](int l, int r) {
        vector<long long> s = {0};
        for (int i = l; i < r; i++) {
            int z = s.size();
            for (int j = 0; j < z; j++)
                s.push_back((s[j] + a[i]) % mod);
        }
        return s;
    };
    auto l = enumerate(0, n / 2), r = enumerate(n / 2, n);
    sort(r.begin(), r.end());
    long long ans = 0;
    for (long long x : l) {
        auto it = upper_bound(r.begin(), r.end(), mod - 1 - x);
        if (it != r.begin())
            ans = max(ans, x + *prev(it));
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

两半都包含空集；先取余；upper_bound 返回位置，取前驱前检查边界。
