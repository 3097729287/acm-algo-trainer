## P3080 The Cow Run G/S

原题：[P3080](https://www.luogu.com.cn/problem/P3080)

### 从问题到算法

沿数轴走到一个点时，会经过沿途所有奶牛，立即安抚不会变差。因此已安抚点必构成排序后连续区间，只需从当前区间向左或向右扩展一头。

设区间长度为 len，其中一个是起点零，已安抚 len−1 头，仍有 n−len+1 头每分钟造成损失。向新端点移动距离 d，新增损失就是 d·(n−len+1)，无论最终访问顺序如何都应在这段移动中支付。

dp[l][r][0/1] 分别记录停在左右端的最小损失，初始仅零位置为零。按区间长度递增更新，转移只有四种距离计算。全部包含后取两端状态较小值。

### 复杂度

时间 O(n²)，空间 O(n²)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> a(n + 1);
    for (int i = 0; i < n; i++)
        cin >> a[i];
    a[n] = 0;
    sort(a.begin(), a.end());
    int N = n + 1, start = lower_bound(a.begin(), a.end(), 0) - a.begin();
    const long long INF = 1LL << 62;
    vector<vector<array<long long, 2>>> dp(N, vector<array<long long, 2>>(N, {INF, INF}));
    dp[start][start] = {0, 0};
    for (int len = 1; len <= N; len++)
        for (int l = 0; l + len <= N; l++) {
            int r = l + len - 1;
            if (l > start || r < start)
                continue;
            long long remaining = N - len;
            for (int side = 0; side < 2; side++)
                if (dp[l][r][side] < INF) {
                    int pos = side ? r : l;
                    if (l)
                        dp[l - 1][r][0] =
                            min(dp[l - 1][r][0], dp[l][r][side] + (a[pos] - a[l - 1]) * remaining);
                    if (r + 1 < N)
                        dp[l][r + 1][1] =
                            min(dp[l][r + 1][1], dp[l][r][side] + (a[r + 1] - a[pos]) * remaining);
                }
        }
    cout << min(dp[0][n][0], dp[0][n][1]) << '\n';

    return 0;
}
```

### 实现提醒

零是虚拟起点，不是奶牛；增加损失乘所有未安抚奶牛；从区间当前端点量路程。
