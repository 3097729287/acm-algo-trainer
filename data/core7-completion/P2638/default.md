## P2638 安全系统

原题：[P2638](https://www.luogu.com.cn/problem/P2638)

### 思路

把没有使用的零也看成放在一个额外储存区，分配 a 个相同零到 n+1 区有 C(n+a,n) 种。一的分配独立，答案为 C(n+a,n)·C(n+b,n)。

### 复杂度

时间 O(50²)，空间 O(50²)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, a, b;
    cin >> n >> a >> b;
    __int128 C[51][51]{};
    for (int i = 0; i <= 50; i++) {
        C[i][0] = C[i][i] = 1;
        for (int j = 1; j < i; j++)
            C[i][j] = C[i - 1][j - 1] + C[i - 1][j];
    }
    __int128 ans = C[n + a][n] * C[n + b][n];
    string out;
    do {
        out += char('0' + ans % 10);
        ans /= 10;
    } while (ans);
    reverse(out.begin(), out.end());
    cout << out << '\n';

    return 0;
}
```

### 实现提醒

未用信号也参与一一对应；两种信号独立；答案不能只用 unsigned long long。
