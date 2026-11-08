## P2180 摆石子

原题：[P2180](https://www.luogu.com.cn/problem/P2180)

### 从问题到算法

任意两列贡献的矩形数等于它们共有石子行中任取两行的数量。把各列石子向同一侧对齐，会使共有行数达到两列高度的较小值，矩形数不会减少；行方向也可做同样压缩。

压缩后的边界呈阶梯。对相邻未满部分进行石子转移时，矩形数随转移量是凸的二次式，因此极值可以向端点推进，直至某一部分填满或清空。反复整理，最优可在“满矩形加一行或一列”的形状中取得。两个方向都要枚举。

固定满列高度 h，q 个满列各有 h 枚石子，另有 r 枚在一个短列。两个满列选两行贡献 C(h,2)，满列对数为 C(q,2)；短列与每个满列共有 r 行，额外贡献 qC(r,2)。检查 q 不超过可用列数，若 r>0 还须有多余一列。

K=0 或不足组成一个矩形时，公式自然得到零。枚举 h 不超过相应维度，矩形计数使用 long long。

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
