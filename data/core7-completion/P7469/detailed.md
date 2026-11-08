## P7469 积木小赛

原题：[P7469](https://www.luogu.com.cn/problem/P7469)

### 从问题到算法

这里按最后剩下的字符序列区分情况，同一个字符串的多种选取位置不另算。直接统计子序列匹配方式会超过题目答案。

为 s 建 next[pos][c]，表示 pos 及之后第一个字符 c。对 t 的每个起点向右扫描，始终匹配 s 中最早可用位置，这会为后续字符留下最多空间；第一次无法匹配后，更长前缀也不可能匹配。得到 valid[i]，表示后缀 t[i..] 的前 valid[i] 个前缀字符串合法。

把 t 的后缀排序。当前后缀与之前任一后缀共享的最长前缀，等于它与紧邻前驱的 LCP。凡共享且在当前合法长度内的字符串，在前驱处也合法，因为它们内容完全相同。因此当前新增数为 max(0,valid[i]−LCP)。

n≤3000，可直接用平方 LCP 表，使后缀比较为常数时间，整个过程确定性去重，不依赖字符串哈希。

### 复杂度

时间 O(n²+n log n)，空间 O(n²)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    string s, t;
    cin >> n >> s >> t;
    vector<array<int, 26>> next(n + 1);
    next[n].fill(n);
    for (int i = n - 1; i >= 0; i--) {
        next[i] = next[i + 1];
        next[i][s[i] - 'a'] = i;
    }
    vector<int> valid(n), sa(n);
    for (int i = 0; i < n; i++) {
        int pos = 0;
        for (int j = i; j < n; j++) {
            pos = next[pos][t[j] - 'a'];
            if (pos == n)
                break;
            valid[i]++;
            pos++;
        }
        sa[i] = i;
    }
    vector<vector<unsigned short>> lcp(n + 1, vector<unsigned short>(n + 1));
    for (int i = n - 1; i >= 0; i--)
        for (int j = n - 1; j >= 0; j--)
            if (t[i] == t[j])
                lcp[i][j] = lcp[i + 1][j + 1] + 1;
    sort(sa.begin(), sa.end(), [&](int a, int b) {
        int same = lcp[a][b];
        if (a + same == n || b + same == n)
            return n - a < n - b;
        return t[a + same] < t[b + same];
    });
    long long ans = 0;
    for (int i = 0; i < n; i++)
        ans += max(0, valid[sa[i]] - (i ? lcp[sa[i]][sa[i - 1]] : 0));
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

按剩余字符串去重；子序列贪心取最早位置；valid 不计空串。
