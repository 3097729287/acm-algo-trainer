## P1123 取数游戏

原题：[P1123](https://www.luogu.com.cn/problem/P1123)

### 思路

每行用二进制掩码表示选中的列，先排除本行相邻的选择。相邻两行的掩码还必须在同列及左右斜列都不冲突，再做最大和动态规划。

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
