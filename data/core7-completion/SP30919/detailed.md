## SP30919 GCDS - Sabbir and gcd problem

原题：[SP30919](https://www.luogu.com.cn/problem/SP30919)

### 从问题到算法

设最优 x 为合数，取它的一个质因数 p<x。若某个输入能被 p 整除，则它与 x 的 gcd 也至少为 p，与 x 合法矛盾；所以 p 本身也合法，违背 x 最小。因此只需考虑质数。

预处理至最大输入值范围的最小质因数，读取每个数后不断按最小质因数剥除，并把出现过的质数标记。一个质数 p 合法，当且仅当没有任何输入含 p 这个因子。按质数递增找第一个未标记者即可。

同一数的一个质因子出现多次只需标一次；输入为一不带任何质因子。筛到 10000010，包含超过全部允许输入的下一个质数，保证能找到未出现的候选。

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
