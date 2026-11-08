## P3435 OKR-Periods of Words

原题：[P3435](https://www.luogu.com.cn/problem/P3435)

### 从问题到算法

若长度为 len 的前缀存在长度 b 的真 border，就满足首 b 个字符等于末 b 个字符，相应可选重复结构的块长为 len−b。要让块最长，就应取最短的非空 border。

最长 border 为 pi[len−1]，其它 border 正好沿着这个前缀的 border 链继续回退。令 shortest[len] 为最短非空 border：没有 border 时为零；若最长 border 本身没有更短 border，则取它；否则复用 shortest[最长border]。

按长度递增计算，依赖总是已经算好的更短前缀。对有 border 的前缀把 len−shortest[len] 累加，没有 border 则贡献零。总答案可能二次增长，要用 long long。

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
