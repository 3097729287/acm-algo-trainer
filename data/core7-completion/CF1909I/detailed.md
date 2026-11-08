## CF1909I Short Permutation Problem

原题：[CF1909I](https://www.luogu.com.cn/problem/CF1909I)

### 从问题到算法

称相邻和至少为 m 的边为好边。[官方题解](https://codeforces.com/blog/entry/123584) 给出的关键是按大小交替插入，使新元素相对于已插入元素具有统一的好坏关系。下面推导本文使用的剩余元素公式。

固定 m，令 L=m−1。m 为偶数时按 m/2,m/2−1,m/2+1,… 插入 1 到 L；m 为奇数时按 (m−1)/2,(m+1)/2,(m−3)/2,… 插入。两种序列都以一个大元素结束，之后 L+1 到 n 全是大元素。只需维护“第二个插入大元素”与“第二个插入小元素”两份交替 DP。

已有 i 个元素、j 条好边。插入大元素时，两个端点与 j 个好边空隙产生 j+1 条好边，共 j+2 个位置；其余 i−1−j 个坏边空隙产生 j+2 条好边。插入小元素时，两个端点与坏边空隙保持 j，共 i+1−j 个位置；j 个好边空隙则把好边数减一。逐项更新即可。

接下来固定前 L 个元素的一种排列，设它有 b 条坏边，还要插入 r=n−L 个互不相同的大元素。最终恰留 t 条坏边，须从 b 条中选 t 条不放新元素，其余 b−t 条必须至少放一个；其它空隙任意。隔板法给出填入数目的方案 C(n−b,L−t)，新元素在这些空隙中的排列有 r! 种。因此贡献系数为 C(b,t)·r!·C(n−b,L−t)。

设 D[b] 为初始有 b 条坏边的排列数。令 A[b]=D[b]·b!·(n−b)!，B[d]=1/(d!·(r−d)!)，则最终 t 条坏边的数目为 r!/(t!(L−t)!) 乘 Σ(d=0..r)A[t+d]B[d]。把 A 反转，这个相关和就是卷积在 L−1−t 处的系数。使用模 998244353 的 NTT 求出所有 t，最后 k=n−1−t。

各 a(m,k) 必须先在 998244353 下规范成非负代表，再当普通整数参与模 1000000007 的哈希。两种模数不能混算，也不能直接对未取第一个模的真实计数计算第二个模。

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
