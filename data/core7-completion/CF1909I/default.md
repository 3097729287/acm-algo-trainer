## CF1909I Short Permutation Problem

原题：[CF1909I](https://www.luogu.com.cn/problem/CF1909I)

### 思路

令 L=m−1，先交替插入 [1,L] 内的大小元素，使每次新数与此前所有数的和要么全部达标、要么全部不达标。两种奇偶插入序列共用 DP；剩余 n−L 个大数按空隙分配计数，转成一次卷积，得到每个 k 的答案。

固定阈值四，从 [2,1,3] 的一条好边开始。四个空隙中，三个使好边数加一，一个使好边数加二，分别验证转移系数 j+2 与 i−1−j。

![插入最大值时，好边数如何改变](assets/good-edge-insertion.svg)

### 复杂度

时间 O(n² log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

const int NTT_MOD = 998244353;
int modPower(int a, int b) {
    int answer = 1;
    for (; b; b >>= 1, a = 1LL * a * a % NTT_MOD)
        if (b & 1)
            answer = 1LL * answer * a % NTT_MOD;
    return answer;
}
struct Transform {
    int n;
    vector<int> rev, roots;
    Transform(int n) : n(n), rev(n), roots(n) {
        for (int i = 1; i < n; i++)
            rev[i] = (rev[i >> 1] >> 1) | ((i & 1) * (n / 2));
        roots[1] = 1;
        for (int length = 2; length < n; length *= 2) {
            int z = modPower(3, (NTT_MOD - 1) / (2 * length));
            for (int i = length / 2; i < length; i++) {
                roots[2 * i] = roots[i];
                roots[2 * i + 1] = 1LL * roots[i] * z % NTT_MOD;
            }
        }
    }
    void apply(vector<int> &a) {
        for (int i = 0; i < n; i++)
            if (i < rev[i])
                swap(a[i], a[rev[i]]);
        for (int length = 1; length < n; length *= 2)
            for (int start = 0; start < n; start += 2 * length)
                for (int j = 0; j < length; j++) {
                    int x = a[start + j],
                        y = 1LL * a[start + j + length] * roots[length + j] % NTT_MOD;
                    int sum = x + y;
                    if (sum >= NTT_MOD)
                        sum -= NTT_MOD;
                    int difference = x - y;
                    if (difference < 0)
                        difference += NTT_MOD;
                    a[start + j] = sum;
                    a[start + j + length] = difference;
                }
    }
    void inverse(vector<int> &a) {
        reverse(a.begin() + 1, a.end());
        apply(a);
        int inverseN = modPower(n, NTT_MOD - 2);
        for (int &v : a)
            v = 1LL * v * inverseN % NTT_MOD;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long x;
    cin >> n >> x;
    const int mod = 998244353;
    const long long hashMod = 1000000007;
    vector<int> fact(n + 1, 1), inv(n + 1, 1);
    for (int i = 1; i <= n; i++)
        fact[i] = 1LL * fact[i - 1] * i % mod;
    inv[n] = modPower(fact[n], mod - 2);
    for (int i = n; i; i--)
        inv[i - 1] = 1LL * inv[i] * i % mod;
    int size = 1;
    while (size < n + 1)
        size *= 2;
    Transform transform(size);
    vector<int> even(n + 1), odd(n + 1);
    even[0] = odd[0] = 1;
    vector<long long> xp(n + 1, 1);
    x %= hashMod;
    for (int i = 1; i <= n; i++)
        xp[i] = xp[i - 1] * x % hashMod;
    long long rowFactor = 1;
    for (int i = 0; i < 3; i++)
        rowFactor = rowFactor * xp[n] % hashMod;
    long long answer = 0;
    auto step = [&](const vector<int> &dp, int length, bool big) {
        vector<int> next(n + 1);
        int old = length - 1;
        for (int j = 0; j < old; j++)
            if (dp[j]) {
                if (big) {
                    next[j + 1] = (next[j + 1] + 1LL * dp[j] * (j + 2)) % mod;
                    if (j + 2 <= n)
                        next[j + 2] = (next[j + 2] + 1LL * dp[j] * (old - 1 - j)) % mod;
                } else {
                    next[j] = (next[j] + 1LL * dp[j] * (old + 1 - j)) % mod;
                    if (j)
                        next[j - 1] = (next[j - 1] + 1LL * dp[j] * j) % mod;
                }
            }
        return next;
    };
    for (int length = 2; length <= n; length++) {
        even = step(even, length, length % 2 == 0);
        odd = step(odd, length, length % 2 == 1);
        const auto &dp = length % 2 == 0 ? even : odd;
        int remaining = n - length;
        vector<int> a(size), b(size);
        for (int bad = 0; bad < length; bad++)
            a[length - 1 - bad] =
                1LL * dp[length - 1 - bad] * fact[bad] % mod * fact[n - bad] % mod;
        for (int d = 0; d <= remaining; d++)
            b[d] = 1LL * inv[d] * inv[remaining - d] % mod;
        if (remaining) {
            transform.apply(a);
            transform.apply(b);
            for (int i = 0; i < size; i++)
                a[i] = 1LL * a[i] * b[i] % mod;
            transform.inverse(a);
        } else {
            int multiplier = b[0];
            for (int &v : a)
                v = 1LL * v * multiplier % mod;
        }
        long long row = 0;
        for (int bad = 0; bad < length; bad++) {
            int value = 1LL * a[length - 1 - bad] * fact[remaining] % mod * inv[bad] % mod *
                        inv[length - bad] % mod;
            int good = n - 1 - bad;
            row = (row + value * xp[good]) % hashMod;
        }
        answer = (answer + row * rowFactor) % hashMod;
        rowFactor = rowFactor * xp[n] % hashMod;
    }
    cout << answer << '\n';

    return 0;
}
```

### 实现提醒

奇偶 m 对应两种交替序列；最终 k=n−1−t；两种模数按题意分开。
