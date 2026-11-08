## P1123 取数游戏

原题：[P1123](https://www.luogu.com.cn/problem/P1123)

### 从问题到算法

一行最多六格，能用一个小整数完整表示选择。若 mask 与 mask<<1 有公共位，说明同一行有相邻格，不能使用。

设上一行选 prev，本行选 cur。竖直、左斜、右斜冲突分别对应 cur&prev、cur&(prev<<1)、cur&(prev>>1)，三者都必须为零。不相邻的行之间没有限制，所以状态只需记上一行的掩码。

令 dp[mask] 为处理完上一行、其选择为 mask 的最大和；枚举所有相容的前后掩码更新。初始空行只允许掩码零，答案是最后一行所有状态的最大值。这个转移覆盖所有合法选择，并只产生合法选择。

### 复杂度

设合法行状态数为 S，时间 O(T·N·S²)，空间 O(S+NM)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        int n, m;
        cin >> n >> m;
        vector<vector<int>> a(n, vector<int>(m));
        for (auto &r : a)
            for (int &x : r)
                cin >> x;
        vector<int> states;
        for (int s = 0; s < (1 << m); s++)
            if (!(s & (s << 1)))
                states.push_back(s);
        int z = states.size();
        vector<long long> dp(z, LLONG_MIN / 4);
        dp[0] = 0;
        for (int i = 0; i < n; i++) {
            vector<long long> ndp(z, LLONG_MIN / 4);
            for (int j = 0; j < z; j++) {
                int cur = states[j];
                long long sum = 0;
                for (int c = 0; c < m; c++)
                    if (cur >> c & 1)
                        sum += a[i][c];
                for (int k = 0; k < z; k++) {
                    int pre = states[k];
                    if (!(cur & pre) && !(cur & (pre << 1)) && !(cur & (pre >> 1)))
                        ndp[j] = max(ndp[j], dp[k] + sum);
                }
            }
            dp.swap(ndp);
        }
        cout << *max_element(dp.begin(), dp.end()) << '\n';
    }

    return 0;
}
```

### 实现提醒

对角线也算相邻；允许一格不选；每组数据清空状态。
