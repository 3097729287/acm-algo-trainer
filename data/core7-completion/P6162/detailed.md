## P6162 四角链

原题：[P6162](https://www.luogu.com.cn/problem/P6162)

### 从问题到算法

把格子编号看作列，填入的数看作行。每列至多填一个数，对应每列至多一辆车；数字互不相同对应每行至多一辆车。允许区域正好是列高依次为 1 到 n−1 的阶梯棋盘。

其车数递推满足 R(n,k)=R(n−1,k)+(n−k)R(n−1,k−1)：最后一列不放，或放在未占用的行。代换 m=n−k 后，正是第二类 Stirling 数递推 S(n,m)=S(n−1,m−1)+mS(n−1,m)，边界也一致，故答案为 S(n,n−k)。

令 m=n−k，使用满射容斥：m!S(n,m)=Σ(i=0..m)(−1)^(m−i)C(m,i)i^n。将组合数约去 m!，每项是 (−1)^(m−i)i^n/(i!(m−i)!)，预处理阶乘逆元后快速幂求和即可。

### 复杂度

时间 O((n−k) log n)，空间 O(n−k)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

long long power(long long a, long long b, long long mod) {
    long long r = 1;
    for (; b; b >>= 1, a = a * a % mod)
        if (b & 1)
            r = r * a % mod;
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    cin >> n >> k;
    const long long mod = 998244353;
    if (k == 0) {
        cout << 1 << '\n';
        return 0;
    }
    int m = n - k;
    vector<long long> fact(m + 1, 1), inv(m + 1, 1);
    for (int i = 1; i <= m; i++)
        fact[i] = fact[i - 1] * i % mod;
    inv[m] = power(fact[m], mod - 2, mod);
    for (int i = m; i; i--)
        inv[i - 1] = inv[i] * i % mod;
    long long ans = 0;
    for (int i = 0; i <= m; i++) {
        long long term = power(i, n, mod) * inv[i] % mod * inv[m - i] % mod;
        if ((m - i) & 1)
            ans = (ans - term + mod) % mod;
        else
            ans = (ans + term) % mod;
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

是 S(n,n−k)；容斥正负按 m−i；k=0 时答案为 1。
