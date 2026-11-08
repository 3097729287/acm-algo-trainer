## P5694 陨石的秘密

原题：[P5694](https://www.luogu.com.cn/problem/P5694)

### 从问题到算法

令 F[d][a][b][c] 为深度≤d，三类括号对数分别为 a、b、c 的 SS 串数。空串对任意上界都有一种，d=0 的其它状态为零。

非空串第一字符必是某种左括号，它匹配的右括号位置唯一，将全串分成“外括号包住的内部 A”与“后缀 B”。内部深度≤d−1，后缀深度≤d。若外层是大括号，内部可使用三类；若是中括号，内部不能有大括号；若是小括号，内部只能有小括号。枚举内部各类对数，其余对数自动留给后缀，乘两个状态数。

按 d 递增、各括号对数递增计算。后缀总对数更少，所以同一深度的依赖已经就绪。第一对分解唯一，避免按任意拼接点反复计数。最后 F[D]−F[D−1] 得到深度恰好 D，模 11380。

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
