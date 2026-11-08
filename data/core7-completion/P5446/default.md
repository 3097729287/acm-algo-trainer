## P5446 绿绿和串串

原题：[P5446](https://www.luogu.com.cn/problem/P5446)

### 思路

初始长度 m>1 时，反复翻转得到周期 2(m−1) 的无限镜像串。候选 m 必须满足这个周期，并且以 m−1 为中心的可见部分是回文；用 Z 函数与 Manacher 常数时间检查每个 m。

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
