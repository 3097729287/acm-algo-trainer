## P1659 拉拉队排练

原题：[P1659](https://www.luogu.com.cn/problem/P1659)

### 思路

Manacher 求每个中心的最大奇回文长度。某中心也贡献所有更短的正奇数长度，因此从大到小扫描奇数长度并累加中心数，取前 K 个长度做快速幂乘积。

### 复杂度

时间 O(n+n log K)，空间 O(n)。

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

    int n;
    long long K;
    string s;
    cin >> n >> K >> s;
    auto [odd, even] = manacher(s);
    vector<long long> cnt(n + 1);
    for (int r : odd)
        cnt[2 * r - 1]++;
    const long long P = 19930726;
    auto power = [&](long long a, long long b) {
        long long r = 1;
        for (; b; b >>= 1, a = a * a % P)
            if (b & 1)
                r = r * a % P;
        return r;
    };
    long long active = 0, ans = 1;
    for (int length = n % 2 ? n : n - 1; length >= 1; length -= 2) {
        active += cnt[length];
        long long take = min(K, active);
        ans = ans * power(length, take) % P;
        K -= take;
        if (!K)
            break;
    }
    cout << (K ? -1 : ans) << '\n';

    return 0;
}
```

### 实现提醒

只统计奇回文；频次要向短长度累加；K 可能达到万亿。
