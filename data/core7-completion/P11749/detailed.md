## P11749 Standard Problem.

原题：[P11749](https://www.luogu.com.cn/problem/P11749)

### 从问题到算法

所有回文按中心计数，一个中心贡献的回文数就是它的半径。周期串中，同一相位的两边字符比较以 n 为周期；连续一个周期都相等后，后续比较永远相等，否则最大半径在这个周期内已经确定。

对 sss 的中间一份求奇偶半径。奇半径包含中心，达到 n+1 即确认无限；偶半径达到 n 即确认无限。这些阈值在中间一份各中心都不会被字符串边界阻止。其它半径为有限 R。

设相位 r 的第 j 个中心在 i=r+jn，总长 L=nk。奇中心实际贡献 min(R,i+1,L−i)，偶中心为 min(R,i,L−i)。有限 R 不超过一个周期，k≥2 时中间 k−2 块直接各贡献 R，首尾分别截断；k=1 单独取三者最小。

无限 R 时，只需求 min(r+offset+jn,L−r−jn) 的和，offset 奇时为一、偶时为零。两项一个递增一个递减，在唯一交点处分开，两边各是等差数列，常数时间计算。遍历 n 个相位相加，避免构造长度可能达三千万亿的 t。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

pair<vector<int>, vector<int>> manacher(const string &s) {
    int n = s.size();
    vector<int> odd(n), even(n);
    for (int i = 0, l = 0, r = -1; i < n; i++) {
        int k = i > r ? 1 : min(odd[l + r - i], r - i + 1);
        while (i - k >= 0 && i + k < n && s[i - k] == s[i + k])
            k++;
        odd[i] = k;
        if (i + k - 1 > r) {
            l = i - k + 1;
            r = i + k - 1;
        }
    }
    for (int i = 0, l = 0, r = -1; i < n; i++) {
        int k = i > r ? 0 : min(even[l + r - i + 1], r - i + 1);
        while (i - k - 1 >= 0 && i + k < n && s[i - k - 1] == s[i + k])
            k++;
        even[i] = k;
        if (i + k - 1 > r) {
            l = i - k;
            r = i + k - 1;
        }
    }
    return {move(odd), move(even)};
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    const long long P = 998244353;
    while (T--) {
        int n;
        long long k;
        string s;
        cin >> n >> k >> s;
        string triple = s + s + s;
        auto [odd, even] = manacher(triple);
        long long length = 1LL * n * k, ans = 0;
        auto contribution = [&](int r, int R, int offset, bool infinite) -> long long {
            if (!infinite) {
                if (k == 1)
                    return min({R, r + offset, n - r});
                return (((k - 2) % P) * R + min(R, r + offset) + min(R, n - r)) % P;
            }
            long long threshold = length - 2LL * r - offset;
            long long left = threshold < 0 ? 0 : min(k, threshold / (2LL * n) + 1);
            long long right = k - left;
            __int128 total = (__int128)left * (r + offset) + (__int128)n * left * (left - 1) / 2 +
                             (__int128)right * (length - r) -
                             (__int128)n * (left + k - 1) * right / 2;
            return total % P;
        };
        for (int r = 0; r < n; r++) {
            ans = (ans + contribution(r, odd[n + r], 1, odd[n + r] >= n + 1)) % P;
            ans = (ans + contribution(r, even[n + r], 0, even[n + r] >= n)) % P;
        }
        cout << ans << '\n';
    }

    return 0;
}
```

### 实现提醒

奇偶中心的左边界差一；中间 s 的半径才够完整；等差乘积使用 __int128。
