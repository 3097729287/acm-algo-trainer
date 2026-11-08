## P2375 动物园

原题：[P2375](https://www.luogu.com.cn/problem/P2375)

### 从问题到算法

长度为 len 的前缀中，前后缀不重叠等价于 border 长度不超过 len/2。最长 border 的其它 border 也都是原前缀的 border，所以只要找到满足长度限制的最长者 j，所有合法 border 就是 j 自身及它的 border 链。

先求 pi，并令 count[len]=count[pi[len−1]]+1，表示从该前缀自身到最短非空 border 的链长。第二次从左向右维护匹配长度 j，先按 KMP 匹配当前字符，再在 2j>len 时沿 pi 回退。合法 border 数就是 count[j]。

不能对每个前缀都从它完整的最长 border 重新一路退到一半，那在全相同字符中会平方级。第二次扫描复用上一前缀的 j，每步增长至多一，所有回退合计线性。答案乘 count[j]+1，并随时取模。

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
