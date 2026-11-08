## P5446 绿绿和串串

原题：[P5446](https://www.luogu.com.cn/problem/P5446)

### 从问题到算法

令 L=m−1。翻转后的字符按原串下标零、一、……、L、L−1、……、一不断循环，所以周期是 2L；继续翻转只会延长同一无限串的前缀。

候选 m 对应的初始串必是 S 的 m 长前缀。先检查周期：若 2L<n，要求 Z[2L]≥n−2L。再检查第一次折返：以 L 为中心，当前可见范围内必须对称，要求奇回文半径至少 min(L+1,n−L)。

周期保证后续每块都与第一周期一致，回文条件保证第一周期确实是前缀的镜像，因此两个条件充分；它们也显然必要。m=1 时无限串只能是单一字符，单独判断整串是否相同。枚举 m 递增输出。

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

vector<int> zfunction(const string &s) {
    int n = s.size();
    vector<int> z(n);
    z[0] = n;
    for (int i = 1, l = 0, r = 0; i < n; i++) {
        if (i <= r)
            z[i] = min(r - i + 1, z[i - l]);
        while (i + z[i] < n && s[z[i]] == s[i + z[i]])
            z[i]++;
        if (i + z[i] - 1 > r) {
            l = i;
            r = i + z[i] - 1;
        }
    }
    return z;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        string s;
        cin >> s;
        int n = s.size();
        auto z = zfunction(s);
        auto [odd, even] = manacher(s);
        vector<int> ans;
        if (all_of(s.begin(), s.end(), [&](char c) { return c == s[0]; }))
            ans.push_back(1);
        for (int m = 2; m <= n; m++) {
            int L = m - 1;
            if (odd[L] < min(L + 1, n - L))
                continue;
            if (2 * L < n && z[2 * L] < n - 2 * L)
                continue;
            ans.push_back(m);
        }
        for (int i = 0; i < (int)ans.size(); i++)
            cout << ans[i] << (i + 1 == (int)ans.size() ? '\n' : ' ');
    }

    return 0;
}
```

### 实现提醒

镜像不重复末字符；周期是 2(m−1)；长度一单独处理。
