## CF1267K Key Storage

原题：[CF1267K](https://www.luogu.com.cn/problem/CF1267K)

### 思路

依次除以二、三、四所得余数，正是各位上界分别为一、二、三的阶乘进制。统计同一数位多重集合的合法排列，减去最高位为零的排列，再减去原数字。

### 复杂度

每组 O(L log L)，空间 O(L)，L=O(log k/log log k)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        long long k;
        cin >> k;
        vector<int> d;
        for (int base = 2; k; base++) {
            d.push_back(k % base);
            k /= base;
        }
        auto countWays = [&](vector<int> a) {
            int L = a.size();
            sort(a.rbegin(), a.rend());
            __int128 ways = 1;
            vector<int> cnt(22);
            for (int i = 0; i < L; i++) {
                int choices = L - max(1, a[i]) + 1 - i;
                if (choices <= 0)
                    return (long long)0;
                ways *= choices;
                cnt[a[i]]++;
            }
            for (int c : cnt)
                for (int i = 2; i <= c; i++)
                    ways /= i;
            return (long long)ways;
        };
        long long ans = countWays(d);
        auto it = find(d.begin(), d.end(), 0);
        if (it != d.end()) {
            d.erase(it);
            ans -= countWays(d);
        }
        cout << ans - 1 << '\n';
    }

    return 0;
}
```

### 实现提醒

最高位不能为零；相同余数要除重；最后减去原数。
