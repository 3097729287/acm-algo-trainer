## P5686 和积和

原题：[P5686](https://www.luogu.com.cn/problem/P5686)

### 从问题到算法

区间和积为 (A[r]−A[l−1])(B[r]−B[l−1])。将前一个前缀下标记为 j，并展开乘积：ArBr−ArBj−BrAj+AjBj。

固定 r 时，j 有 r 个取值零到 r−1，因此第一项累加为 rArBr，其余三项只需要之前 A 的和、B 的和、A·B 的和。计算本次贡献后再把当前前缀加入统计，避免把空区间混入。

输入先给完整 a 再给 b，可先存 A 前缀，读取 b 时递推 B 并累计答案。每一步取模，负项统一加模数规范化。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007;
long long power(long long a, long long b) {
    long long r = 1;
    for (; b; b >>= 1, a = a * a % MOD)
        if (b & 1)
            r = r * a % MOD;
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> A(n + 1);
    for (int i = 1; i <= n; i++) {
        long long x;
        cin >> x;
        A[i] = (A[i - 1] + x) % MOD;
    }
    long long B = 0, sumA = 0, sumB = 0, sumAB = 0, ans = 0;
    for (int r = 1; r <= n; r++) {
        long long x;
        cin >> x;
        B = (B + x) % MOD;
        long long term = (r * A[r] % MOD * B - A[r] * sumB % MOD - B * sumA % MOD + sumAB) % MOD;
        ans = (ans + term + 2 * MOD) % MOD;
        sumA = (sumA + A[r]) % MOD;
        sumB = (sumB + B) % MOD;
        sumAB = (sumAB + A[r] * B) % MOD;
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

前缀零也在历史中；先计贡献再插入；乘积及时取模。
