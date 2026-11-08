## P3435 OKR-Periods of Words

原题：[P3435](https://www.luogu.com.cn/problem/P3435)

### 思路

对每个前缀，若它存在真 border，最长合法周期块长度等于前缀长度减去最短非空 border 长度。用前缀函数递推每个前缀的最短 border，再求和。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

vector<int> prefix(const string &s) {
    vector<int> p(s.size());
    for (int i = 1; i < (int)s.size(); i++) {
        int j = p[i - 1];
        while (j && s[i] != s[j])
            j = p[j - 1];
        if (s[i] == s[j])
            j++;
        p[i] = j;
    }
    return p;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    string s;
    cin >> n >> s;
    auto p = prefix(s);
    vector<int> shortest(n + 1);
    long long ans = 0;
    for (int len = 1; len <= n; len++) {
        int b = p[len - 1];
        if (b) {
            shortest[len] = shortest[b] ? shortest[b] : b;
            ans += len - shortest[len];
        }
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

这里要最短非空 border；不能只使用最长 border；总和用六十四位。
