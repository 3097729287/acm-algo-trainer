## P3811 模意义下的乘法逆元

原题：[P3811](https://www.luogu.com.cn/problem/P3811)

### 从问题到算法

设 q=floor(p/i)、r=p%i，则 qi+r≡0。因为一到 n 均小于质数 p，i 与 r 都有逆元；对 i>1 有 r>0。两侧乘以 inv[i]inv[r]，得到 inv[i]≡−q·inv[r]。

余数 r<i，因此扫描 i 递增时 inv[r] 已经求出。用 p−q 表示负系数，先做六十四位乘法再取模。这样不用对每个数单独做快速幂。

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
