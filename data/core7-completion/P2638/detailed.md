## P2638 安全系统

原题：[P2638](https://www.luogu.com.cn/problem/P2638)

### 从问题到算法

每个实际储存区可以存任意多个零与一，因此两种信号的数量选择没有相互限制。对零额外设置一个“未使用区”，原来最多使用 a 个的方案就与把恰好 a 个零分配到 n+1 个有标号区一一对应。

非负整数方程 x0+x1+…+xn=a 的解数由隔板法为 C(n+a,n)，一同理。两者独立相乘。

n+a、n+b 都不超过五十，单个组合数能放在六十四位，但两者乘积可能远超六十四位。用 __int128 做 Pascal 递推与最终乘积，再手动输出十进制。

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
