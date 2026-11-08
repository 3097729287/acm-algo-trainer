## P14075 划分字符串

原题：[P14075](https://www.luogu.com.cn/problem/P14075)

### 从问题到算法

任意最优划分都有最后一段。若最后一段是 j..i，前面必须采用前 j−1 字符的最优划分，否则可以替换使总价值更高。因此枚举所有合法最后段即可得到完备转移。

从 i 向左扫描，用二十六位 mask 记录已经出现的字母；遇到重复就停止，更长的段必然也含重复。最多查看二十六个字符，时间不再是平方。

价值并不保证随长度增长，不能贪心尽量切长或尽量切短。动态规划会同时比较全部可能长度，答案使用六十四位。

### 复杂度

时间 O(26n)，空间 O(n)。

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
    vector<long long> a(n + 1), dp(n + 1);
    for (int i = 1; i <= n; i++)
        cin >> a[i];
    for (int i = 1; i <= n; i++) {
        int mask = 0;
        for (int j = i; j >= 1; j--) {
            int bit = 1 << (s[j - 1] - 'a');
            if (mask & bit)
                break;
            mask |= bit;
            dp[i] = max(dp[i], dp[j - 1] + a[i - j + 1]);
        }
    }
    cout << dp[n] << '\n';

    return 0;
}
```

### 实现提醒

长度价值无单调性；重复时立即停止；答案可超过三十二位。
