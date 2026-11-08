## P2180 摆石子

原题：[P2180](https://www.luogu.com.cn/problem/P2180)

### 思路

行列压缩后，同一列的石子可以尽量对齐。最优形状可取一个满矩形，再在一行或一列上放剩余石子。枚举满列高度 h，令 q=K/h、r=K%h，贡献为 C(h,2)C(q,2)+qC(r,2)，再交换两维检查。

### 复杂度

时间 O(N+M)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long n, m, k;
    cin >> n >> m >> k;
    auto choose2 = [](long long x) { return x * (x - 1) / 2; };
    long long answer = 0;
    for (int direction = 0; direction < 2; direction++) {
        for (long long h = 1; h <= n; h++) {
            long long q = k / h, r = k % h;
            if (q > m || (r && q == m))
                continue;
            answer = max(answer, choose2(h) * choose2(q) + q * choose2(r));
        }
        swap(n, m);
    }
    cout << answer << '\n';

    return 0;
}
```

### 实现提醒

两个方向都检查；短列需要额外列位置；取两行两列，使用组合数。
