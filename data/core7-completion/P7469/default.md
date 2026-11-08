## P7469 积木小赛

原题：[P7469](https://www.luogu.com.cn/problem/P7469)

### 思路

枚举 t 的每个起点，贪心匹配 s 中最靠前位置，得到能作为子序列的最大长度。随后按 t 后缀的字典序，用相邻 LCP 扣除已经出现的相同字符串。

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
