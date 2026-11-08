## P5752 棋盘分割

原题：[P5752](https://www.luogu.com.cn/problem/P5752)

### 从问题到算法

展开方差平方，σ²=Σx_i²/n−(总分/n)²，第二项固定。只需使 Σx_i² 最小，最后再开方。二维前缀和让任意矩形总分快速可得。

设 solve(rect,k) 是矩形按原题逐次割下一块的规则分成 k 块的最小平方和。k=1 时为矩形总分平方。枚举一条完整横切或竖切，一侧立即结束为一个块，另一侧继续分 k−1 块；两个方向都要尝试。

不能把任意两边分别分配多个块，因为题目限定每次只从剩余矩形割下一块。记忆化避免重复计算，面积不足 k 的状态设不可行。最终浮点运算前先用整数求最小平方和，减少精度误差。

### 复杂度

棋盘边长固定为八，状态 O(n·8⁴)，每态 O(8) 转移；空间 O(n·8⁴)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
long long memo[15][9][9][9][9];
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    long long pre[9][9]{};
    for (int i = 1; i <= 8; i++)
        for (int j = 1; j <= 8; j++) {
            long long x;
            cin >> x;
            pre[i][j] = x + pre[i - 1][j] + pre[i][j - 1] - pre[i - 1][j - 1];
        }
    memset(memo, -1, sizeof memo);
    auto sum = [&](int a, int b, int c, int d) {
        return pre[c][d] - pre[a - 1][d] - pre[c][b - 1] + pre[a - 1][b - 1];
    };
    const long long INF = 1LL << 60;
    function<long long(int, int, int, int, int)> solve = [&](int k, int a, int b, int c,
                                                             int d) -> long long {
        if ((c - a + 1) * (d - b + 1) < k)
            return INF;
        long long &ans = memo[k][a][b][c][d];
        if (ans >= 0)
            return ans;
        if (k == 1) {
            long long s = sum(a, b, c, d);
            return ans = s * s;
        }
        ans = INF;
        for (int x = a; x < c; x++) {
            long long s = sum(a, b, x, d), t = sum(x + 1, b, c, d);
            ans =
                min({ans, s * s + solve(k - 1, x + 1, b, c, d), t * t + solve(k - 1, a, b, x, d)});
        }
        for (int y = b; y < d; y++) {
            long long s = sum(a, b, c, y), t = sum(a, y + 1, c, d);
            ans =
                min({ans, s * s + solve(k - 1, a, y + 1, c, d), t * t + solve(k - 1, a, b, c, y)});
        }
        return ans;
    };
    long double mean = (long double)pre[8][8] / n;
    long double variance = (long double)solve(n, 1, 1, 8, 8) / n - mean * mean;
    cout << fixed << setprecision(3) << sqrtl(max(0.0L, variance)) << '\n';

    return 0;
}
```

### 实现提醒

只递归继续分一侧；平均值固定；最后按三位小数输出。
