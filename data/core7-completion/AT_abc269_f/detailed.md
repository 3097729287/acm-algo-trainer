## AT_abc269_f Numbered Checker

原题：[AT_abc269_f](https://www.luogu.com.cn/problem/AT_abc269_f)

### 从问题到算法

矩形内有效格可以拆为奇行×奇列与偶行×偶列，两个笛卡尔积不相交。设某类有 nr 行、nc 列，行号减一之和为 sr，列号之和为 sc，则该类总和为 M·sr·nc+sc·nr。

同奇偶的行列是公差为二的等差数列。将起点调整到所需奇偶，算出项数和末项，用“首末项之和乘项数除二”求和；模数为奇质数，可用二的逆元。

每次询问直接处理两个奇偶类，不必枚举格子，也不必存储巨大网格。先将各因子取模再乘，避免原始矩形总和溢出。

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
