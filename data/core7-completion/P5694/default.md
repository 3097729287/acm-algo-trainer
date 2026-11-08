## P5694 陨石的秘密

原题：[P5694](https://www.luogu.com.cn/problem/P5694)

### 思路

先统计深度不超过 D 的串，再减去不超过 D−1 的串。一个非空表达式唯一拆为第一对完整外括号、其内部表达式、以及后续表达式，并按括号种类限制内部可用类型。

### 复杂度

时间 O(D·(L1+1)²(L2+1)²(L3+1)²)，空间 O(D·(L1+1)(L2+1)(L3+1))。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int A, B, C, D;
    cin >> A >> B >> C >> D;
    const int P = 11380;
    int S = (A + 1) * (B + 1) * (C + 1);
    vector<vector<int>> f(D + 1, vector<int>(S));
    auto id = [&](int a, int b, int c) { return (a * (B + 1) + b) * (C + 1) + c; };
    for (int d = 0; d <= D; d++)
        f[d][0] = 1;
    for (int d = 1; d <= D; d++)
        for (int a = 0; a <= A; a++)
            for (int b = 0; b <= B; b++)
                for (int c = 0; c <= C; c++) {
                    if (!a && !b && !c)
                        continue;
                    long long ans = 0;
                    if (a)
                        for (int x = 0; x < a; x++)
                            for (int y = 0; y <= b; y++)
                                for (int z = 0; z <= c; z++)
                                    ans = (ans + 1LL * f[d - 1][id(x, y, z)] *
                                                     f[d][id(a - 1 - x, b - y, c - z)]) %
                                          P;
                    if (b)
                        for (int y = 0; y < b; y++)
                            for (int z = 0; z <= c; z++)
                                ans = (ans + 1LL * f[d - 1][id(0, y, z)] *
                                                 f[d][id(a, b - 1 - y, c - z)]) %
                                      P;
                    if (c)
                        for (int z = 0; z < c; z++)
                            ans =
                                (ans + 1LL * f[d - 1][id(0, 0, z)] * f[d][id(a, b, c - 1 - z)]) % P;
                    f[d][id(a, b, c)] = ans;
                }
    int ans = f[D][id(A, B, C)];
    if (D)
        ans = (ans - f[D - 1][id(A, B, C)] + P) % P;
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

统计上界后作差；第一完整括号唯一拆分；中小括号对内部类型有限制。
