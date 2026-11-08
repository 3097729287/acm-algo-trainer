## UVA11022 String Factoring

原题：[UVA11022](https://www.luogu.com.cn/problem/UVA11022)

### 思路

dp[l][r] 为子串的最小字符权重。枚举切成两段的拼接，也枚举能完整重复构成该子串的较短周期，把它压缩成一个周期的最优表示。

### 复杂度

每串时间 O(n³)，空间 O(n²)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string s;
    while (cin >> s && s != "*") {
        int n = s.size();
        vector<vector<int>> lcp(n + 1, vector<int>(n + 1)), dp(n, vector<int>(n));
        for (int i = n - 1; i >= 0; i--)
            for (int j = n - 1; j >= 0; j--)
                if (s[i] == s[j])
                    lcp[i][j] = lcp[i + 1][j + 1] + 1;
        for (int len = 1; len <= n; len++)
            for (int l = 0; l + len <= n; l++) {
                int r = l + len - 1;
                dp[l][r] = len;
                for (int mid = l; mid < r; mid++)
                    dp[l][r] = min(dp[l][r], dp[l][mid] + dp[mid + 1][r]);
                for (int p = 1; p < len; p++)
                    if (len % p == 0 && lcp[l][l + p] >= len - p)
                        dp[l][r] = min(dp[l][r], dp[l][l + p - 1]);
            }
        cout << dp[0][n - 1] << '\n';
    }

    return 0;
}
```

### 实现提醒

权重不计括号和指数；重复单位可再次分解；星号停止输入。
