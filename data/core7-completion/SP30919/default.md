## SP30919 GCDS - Sabbir and gcd problem

原题：[SP30919](https://www.luogu.com.cn/problem/SP30919)

### 思路

若一个合数与所有输入互质，它的任一质因数也与所有输入互质且更小，所以最优一定是质数。筛最小质因数并标记输入中出现过的全部质因数，取最小未标记者。

### 复杂度

预处理 O(A)，每组分解 O(n log A)，空间 O(A)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    const int limit = 10000010;
    vector<int> least(limit + 1), primes;
    for (int i = 2; i <= limit; i++) {
        if (!least[i]) {
            least[i] = i;
            primes.push_back(i);
        }
        for (int p : primes) {
            if (p > least[i] || 1LL * i * p > limit)
                break;
            least[i * p] = p;
        }
    }
    int tests;
    cin >> tests;
    vector<int> stamp(limit + 1);
    for (int test = 1; test <= tests; test++) {
        int n;
        cin >> n;
        while (n--) {
            int x;
            cin >> x;
            while (x > 1) {
                int p = least[x];
                stamp[p] = test;
                while (x % p == 0)
                    x /= p;
            }
        }
        for (int p : primes)
            if (stamp[p] != test) {
                cout << p << '\n';
                break;
            }
    }

    return 0;
}
```

### 实现提醒

寻找 x>1；质因子去重标记；不要只计算所有数的 gcd。
