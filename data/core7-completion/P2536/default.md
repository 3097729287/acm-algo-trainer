## P2536 病毒检测

原题：[P2536](https://www.luogu.com.cn/problem/P2536)

### 思路

令 dp[j] 表示模式当前前缀能否匹配 DNA 前 j 个字符。普通字符或 ? 从上一行 j−1 转移，* 则可不匹配字符，或在本行继续吞掉一个字符。

### 复杂度

时间 O(N·模式长度·DNA长度)，空间 O(DNA长度)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string pattern;
    int n;
    cin >> pattern >> n;
    int ans = 0;
    while (n--) {
        string s;
        cin >> s;
        vector<char> dp(s.size() + 1), next(s.size() + 1);
        dp[0] = 1;
        for (char c : pattern) {
            fill(next.begin(), next.end(), 0);
            if (c == '*') {
                next[0] = dp[0];
                for (int j = 1; j <= (int)s.size(); j++)
                    next[j] = dp[j] || next[j - 1];
            } else
                for (int j = 1; j <= (int)s.size(); j++)
                    next[j] = dp[j - 1] && (c == '?' || c == s[j - 1]);
            dp.swap(next);
        }
        ans += !dp.back();
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

* 可匹配零个字符；星号行从左往右；输出不匹配的数量。
