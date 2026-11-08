## CF1015F Bracket Substring

原题：[CF1015F](https://www.luogu.com.cn/problem/CF1015F)

### 从问题到算法

合法括号序列要求所有前缀余额非负，最终余额为零。模式子串匹配则由 KMP 的最长匹配前缀长度描述，两类信息合并后便足以决定下一步。

预处理每个匹配状态添加左、右括号后的新状态。完整命中后用状态 m 表示“已经出现”，无论后续字符为何都保持 m，避免重复出现被重复计数。

从空串、余额零、匹配零开始，每次尝试两种括号。右括号不能使余额负数，余额也不能超过剩余位置能够关闭的数量。逐位置滚动数组，最后取余额零、吸收状态。每个不同括号串沿唯一状态路线被计一次。

### 复杂度

时间 O(n²|s|)，空间 O(n|s|)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    string s;
    cin >> n >> s;
    int m = s.size();
    const int P = 1000000007;
    vector<int> pi(m);
    for (int i = 1; i < m; i++) {
        int j = pi[i - 1];
        while (j && s[i] != s[j])
            j = pi[j - 1];
        if (s[i] == s[j])
            j++;
        pi[i] = j;
    }
    vector<array<int, 2>> next(m + 1);
    for (int state = 0; state < m; state++)
        for (int c = 0; c < 2; c++) {
            char ch = c ? ')' : '(';
            int j = state;
            while (j && s[j] != ch)
                j = pi[j - 1];
            if (s[j] == ch)
                j++;
            next[state][c] = j;
        }
    next[m] = {m, m};
    vector<vector<int>> dp(n + 1, vector<int>(m + 1));
    dp[0][0] = 1;
    for (int used = 0; used < 2 * n; used++) {
        vector<vector<int>> ndp(n + 1, vector<int>(m + 1));
        for (int balance = 0; balance <= n; balance++)
            for (int state = 0; state <= m; state++)
                if (dp[balance][state])
                    for (int c = 0; c < 2; c++) {
                        int b = balance + (c ? -1 : 1);
                        if (b < 0 || b > n || b > 2 * n - used - 1)
                            continue;
                        int &v = ndp[b][next[state][c]];
                        v += dp[balance][state];
                        if (v >= P)
                            v -= P;
                    }
        dp.swap(ndp);
    }
    cout << dp[0][m] << '\n';

    return 0;
}
```

### 实现提醒

完整命中后吸收；右括号不能造成负余额；计数按序列而非匹配次数。
