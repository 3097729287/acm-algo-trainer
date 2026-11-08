## P11965 等价消除

原题：[P11965](https://www.luogu.com.cn/problem/P11965)

### 思路

任意两个相同字符都可以删除，所以子串能被清空当且仅当每种字母出现偶数次。用二十六位掩码记录前缀奇偶，统计相同掩码的前缀对。

### 复杂度

平均时间 O(n)，空间 O(n)。

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
    unordered_map<int, long long> cnt;
    cnt.reserve(2 * n + 1);
    cnt[0] = 1;
    int mask = 0;
    long long ans = 0;
    for (char c : s) {
        mask ^= 1 << (c - 'a');
        ans += cnt[mask];
        cnt[mask]++;
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

删除字符不要求相邻；空前缀要预先加入；查询计数后再增加当前频次。
