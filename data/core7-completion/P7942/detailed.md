## P7942 CONsecutive and CONcat (easy version)

原题：[P7942](https://www.luogu.com.cn/problem/P7942)

### 从问题到算法

一段同字母若跨过两个边界，中间完整字符串就必须全部相同字母，与 easy version 保证矛盾。因此只有串内与跨一个边界两类。

串内每个长度 L 的连续段贡献 max(0,L−k+1)，它会在所有 n! 个排列中出现。对跨界情况，设左串后缀长 s、右串前缀长 p，且字母同为 c。窗口从左取 u 个、右取 k−u 个，要求 max(1,k−p)≤u≤min(s,k−1)，区间整数数量就是跨界贡献。

按字母及长度统计后缀频次、前缀频次，枚举 s、p 的乘积得到有序对数量；若同一个串同时属于两类，需要减去它与自己配对的计数。每个不同串的有序相邻关系在排列中出现 (n−1)! 次。m≤100，可直接枚举二十六种字母和两种长度。

### 复杂度

时间 O(nm+26m²)，空间 O(26m²+n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, k;
    cin >> n >> m >> k;
    const long long P = 998244353;
    vector<vector<long long>> suffix(26, vector<long long>(m + 1)), prefix = suffix;
    vector<vector<vector<int>>> self(26, vector<vector<int>>(m + 1, vector<int>(m + 1)));
    long long inside = 0;
    for (int i = 0; i < n; i++) {
        string s;
        cin >> s;
        for (int l = 0; l < m;) {
            int r = l + 1;
            while (r < m && s[r] == s[l])
                r++;
            inside += max(0, r - l - k + 1);
            l = r;
        }
        int p = 1, t = 1;
        while (p < m && s[p] == s[0])
            p++;
        while (t < m && s[m - 1 - t] == s[m - 1])
            t++;
        prefix[s[0] - 'a'][p]++;
        suffix[s.back() - 'a'][t]++;
        if (s[0] == s.back())
            self[s[0] - 'a'][t][p]++;
    }
    vector<long long> fact(n + 1, 1);
    for (int i = 1; i <= n; i++)
        fact[i] = fact[i - 1] * i % P;
    long long cross = 0;
    for (int c = 0; c < 26; c++)
        for (int s = 1; s <= m; s++)
            for (int p = 1; p <= m; p++) {
                int ways = max(0, min(s, k - 1) - max(1, k - p) + 1);
                long long pairs = (suffix[c][s] * prefix[c][p] - self[c][s][p]) % P;
                cross = (cross + pairs * ways) % P;
            }
    cout << ((inside % P) * fact[n] + cross * fact[n - 1]) % P << '\n';

    return 0;
}
```

### 实现提醒

仅针对每串非单字母的 easy 保证；跨界两串必须不同编号；相同内容不同编号仍是不同串。
