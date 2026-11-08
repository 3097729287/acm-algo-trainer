## CF757B Bash's Big Day

原题：[CF757B](https://www.luogu.com.cn/problem/CF757B)

### 从问题到算法

若某个合法组的 gcd 大于一，这个 gcd 至少有一个质因数 p，组内每个数都被 p 整除。因此任何合法组的大小，都不超过某个质数倍数的总出现次数。

反过来，把数组中所有 p 的倍数选出来，gcd 至少含因子 p，是合法组。所以逐个质数统计其倍数出现次数便能达到最优。重复的值代表不同位置，出现几次就应计几次。

先建立值域频数，再用筛法找质数并按倍数累加。没有任何可共享的质因数时，题目仍允许保留单个元素，答案至少为一。

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
