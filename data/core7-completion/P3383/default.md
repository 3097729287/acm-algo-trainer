## P3383 线性筛素数

原题：[P3383](https://www.luogu.com.cn/problem/P3383)

### 思路

从小到大扫描，未被标记的数加入质数表。每个合数只由它的最小质因子标记一次，最后第 k 个质数直接访问 primes[k−1]。

### 复杂度

预处理 O(n)，每问 O(1)，空间 O(n) 位加 O(π(n)) 个整数。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<bool> composite(n + 1);
    vector<int> primes;
    for (int i = 2; i <= n; i++) {
        if (!composite[i])
            primes.push_back(i);
        for (int p : primes) {
            long long x = 1LL * i * p;
            if (x > n)
                break;
            composite[x] = 1;
            if (i % p == 0)
                break;
        }
    }
    while (q--) {
        int k;
        cin >> k;
        cout << primes[k - 1] << '\n';
    }

    return 0;
}
```

### 实现提醒

一不是质数；整除时立即 break；先判断六十四位乘积是否越界。
