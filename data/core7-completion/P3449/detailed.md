## P3449 PAL-Palindromes

原题：[P3449](https://www.luogu.com.cn/problem/P3449)

### 从问题到算法

由于 a、b 各自回文，reverse(ab)=reverse(b)reverse(a)=ba。因此 ab 为回文当且仅当 ab=ba。

两个非空字符串可交换拼接，当且仅当它们都是同一个原始串的幂。这个性质可由消去较短前缀反复证明：若 |a|<=|b|，等式迫使 b 以 a 开头，消去这段后得到 a 与剩余部分仍可交换，过程类似欧几里得算法，最终得到共同的最短循环节。

用前缀函数得到候选周期 p=len−pi[len−1]。若 len 能被 p 整除，首 p 个字符就是最小循环节；否则循环节是整个串。按这个实际字符串分组。组内任意有序二元组都合法，包括自己与自己，所以大小 c 的组贡献 c²。

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
