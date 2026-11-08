## P3811 模意义下的乘法逆元

原题：[P3811](https://www.luogu.com.cn/problem/P3811)

### 思路

由 p=(p/i)·i+p%i，在模 p 下整理得到 inv[i]=(p−p/i)·inv[p%i] mod p。从 inv[1]=1 递推即可。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, p;
    cin >> n >> p;
    vector<int> inv(n + 1);
    inv[1] = 1;
    cout << 1 << '\n';
    for (int i = 2; i <= n; i++) {
        inv[i] = 1LL * (p - p / i) * inv[p % i] % p;
        cout << inv[i] << '\n';
    }

    return 0;
}
```

### 实现提醒

质数且 n<p 保证逆元存在；inv[1]=1；乘法用 long long。
