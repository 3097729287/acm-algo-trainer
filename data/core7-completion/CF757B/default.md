## CF757B Bash's Big Day

原题：[CF757B](https://www.luogu.com.cn/problem/CF757B)

### 思路

一组数的 gcd 大于 1，当且仅当存在一个质数整除组内所有数。统计每个质数的倍数在数组中出现多少次，取最大值即可；全为 1 时仍可选一个数。

### 复杂度

时间 O(A log log A)，空间 O(A)，A 为最大值。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> a(n);
    int limit = 1;
    for (int &x : a) {
        cin >> x;
        limit = max(limit, x);
    }
    vector<int> freq(limit + 1);
    for (int x : a)
        freq[x]++;
    vector<char> composite(limit + 1);
    int ans = 1;
    for (int p = 2; p <= limit; p++)
        if (!composite[p]) {
            int total = 0;
            for (int j = p; j <= limit; j += p) {
                total += freq[j];
                if (j > p)
                    composite[j] = 1;
            }
            ans = max(ans, total);
        }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

统计出现次数而非不同值数；答案至少为 1。
