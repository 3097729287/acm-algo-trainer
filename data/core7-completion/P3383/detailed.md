## P3383 线性筛素数

原题：[P3383](https://www.luogu.com.cn/problem/P3383)

### 从问题到算法

处理整数 i 时，按升序枚举已发现质数 p，标记 i·p。当 p 整除 i 后立即停止：之后更大的质数不再是 i·p 的最小质因子，应交由其它整数处理。

每个合数 x 唯一对应 p=最小质因子、i=x/p，且这对会在停止条件之前被枚举，所以每个合数恰好标记一次。未标记数就是质数，扫描顺序保证质数表递增。

范围达到一亿，标记使用位压缩的 vector<bool>，质数表仍保存整数。乘积用六十四位判断边界，查询使用一开始的序号。

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
