## P14075 划分字符串

原题：[P14075](https://www.luogu.com.cn/problem/P14075)

### 思路

合法子串不含重复小写字母，长度最多二十六。令 dp[i] 为前 i 字符的最大划分价值，向左枚举不重复的最后一段，更新 dp[i]=max(dp[j]+a[i−j])。

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
