## AT_abc269_f Numbered Checker

原题：[AT_abc269_f](https://www.luogu.com.cn/problem/AT_abc269_f)

### 思路

保留的格子满足行列同奇偶。对奇行奇列、偶行偶列两类，分别用等差数列求行号减一之和、列号之和，再组合 (行号−1)·M+列号。

### 复杂度

每问 O(1)，额外空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long N, M;
    int Q;
    cin >> N >> M >> Q;
    const long long P = 998244353, INV2 = (P + 1) / 2;
    auto range = [&](long long l, long long r, int parity) {
        if (l % 2 != parity)
            l++;
        if (l > r)
            return pair<long long, long long>{0, 0};
        long long count = (r - l) / 2 + 1, last = l + 2 * (count - 1);
        long long sum = (l + last) % P * (count % P) % P * INV2 % P;
        return pair<long long, long long>{count % P, sum};
    };
    while (Q--) {
        long long A, B, C, D;
        cin >> A >> B >> C >> D;
        long long ans = 0;
        for (int parity = 0; parity < 2; parity++) {
            auto [nr, sr] = range(A, B, parity);
            auto [nc, sc] = range(C, D, parity);
            sr = (sr - nr + P) % P;
            ans = (ans + (M % P) * sr % P * nc + sc * nr) % P;
        }
        cout << ans << '\n';
    }

    return 0;
}
```

### 实现提醒

保留行列同奇偶；列公式使用原始 M；乘法中间及时取模。
