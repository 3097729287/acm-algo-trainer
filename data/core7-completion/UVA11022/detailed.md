## UVA11022 String Factoring

原题：[UVA11022](https://www.luogu.com.cn/problem/UVA11022)

### 从问题到算法

表示式的最外层要么是两个表示式拼接，要么是一个表示式重复。前者枚举分割点，代价为左右区间 dp 之和；后者需要某个长度 p 整除区间长，且整段每隔 p 个字符一致，代价就是第一个周期的 dp。

原题权重只计字母，不计括号与指数，因此重复压缩不额外加数字长度或括号长度。重复单位内部还能继续压缩，这正是使用 dp 而非直接用 p 的原因。

按区间长度递增，所有依赖的区间更短，归纳得到最优值。可以用预处理的任意两后缀 LCP 常数时间检查某个 p 是否为完整周期。详见[原题权重定义](https://onlinejudge.org/external/110/11022.pdf)。

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
