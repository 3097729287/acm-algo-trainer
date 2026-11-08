## P2375 动物园

原题：[P2375](https://www.luogu.com.cn/problem/P2375)

### 思路

先用前缀函数计算每个前缀的 border 链长度，再用第二次 KMP 扫描维护不超过当前长度一半的最长 border。它的整条 border 链都合法，按题意将数量加一后相乘。

### 复杂度

每组时间 O(n)，空间 O(n)。

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

    int tests;
    cin >> tests;
    while (tests--) {
        string s;
        cin >> s;
        int n = s.size();
        auto p = prefix(s);
        vector<int> count(n + 1);
        for (int len = 1; len <= n; len++)
            count[len] = count[p[len - 1]] + 1;
        long long ans = 1;
        int j = 0;
        for (int len = 2; len <= n; len++) {
            while (j && s[len - 1] != s[j])
                j = p[j - 1];
            if (s[len - 1] == s[j])
                j++;
            while (2 * j > len)
                j = p[j - 1];
            ans = ans * (count[j] + 1) % 1000000007;
        }
        cout << ans << '\n';
    }

    return 0;
}
```

### 实现提醒

count[0]=0；先限制不重叠，再乘数量加一；模数为 1000000007。
