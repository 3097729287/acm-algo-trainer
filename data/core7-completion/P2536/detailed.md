## P2536 病毒检测

原题：[P2536](https://www.luogu.com.cn/problem/P2536)

### 从问题到算法

模式中的星号可以匹配任意长度，不能把它当成恰好一个字符。使用逐个模式字符的动态规划可以完整覆盖所有选择。

处理普通字符 c 时，新的 dp[j] 仅能从旧 dp[j−1] 转移，并要求 DNA 第 j 个字符等于 c；问号省略字符相等条件。处理星号时，新的 dp[j] 有两种来源：旧 dp[j] 表示星号匹配空串，新的 dp[j−1] 表示它再匹配一个 DNA 字符。后一项属于本行，必须从左向右计算。

初始空模式只匹配空串。每个 DNA 单独计算，最终 dp[长度] 为假才是非病毒，计入答案。用两行 char 数组滚动，避免为每个片段开完整二维表。

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
