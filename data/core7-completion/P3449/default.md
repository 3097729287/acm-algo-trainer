## P3449 PAL-Palindromes

原题：[P3449](https://www.luogu.com.cn/problem/P3449)

### 思路

两个输入串本来都是回文。它们拼接仍回文当且仅当 ab=ba，即二者都是同一个最小循环节的若干次重复。求每串最小循环节，按内容分组，答案为各组大小平方之和。

### 复杂度

时间 O(L log n)，空间 O(L)，L 为输入总长度。

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
    cin >> n;
    map<string, long long> count;
    while (n--) {
        int len;
        string s;
        cin >> len >> s;
        auto p = prefix(s);
        int period = len - p.back();
        if (len % period)
            period = len;
        count[s.substr(0, period)]++;
    }
    long long ans = 0;
    for (auto &[root, c] : count)
        ans += c * c;
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

输入串已保证回文；只有完整重复时才缩短周期；计有序对与自身配对。
