## AT_abc271_f XOR on Grid Path

原题：[AT_abc271_f](https://www.luogu.com.cn/problem/AT_abc271_f)

### 思路

从左上角走 n−1 步，按终点记录路径异或值的频次；再从右下角反向走 n−1 步。两半在同一个格子相遇时，结合中心格异或值即可查表累计答案。

### 复杂度

平均时间 O(2^n)，空间 O(2^n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<vector<int>> a(n, vector<int>(n));
    for (auto &r : a)
        for (int &x : r)
            cin >> x;
    vector<unordered_map<int, long long>> cnt(n);
    function<void(int, int, int)> go = [&](int x, int y, int v) {
        v ^= a[x][y];
        if (x + y == n - 1) {
            cnt[x][v]++;
            return;
        }
        if (x + 1 < n)
            go(x + 1, y, v);
        if (y + 1 < n)
            go(x, y + 1, v);
    };
    go(0, 0, 0);
    long long ans = 0;
    function<void(int, int, int)> back = [&](int x, int y, int v) {
        v ^= a[x][y];
        if (x + y == n - 1) {
            auto it = cnt[x].find(v ^ a[x][y]);
            if (it != cnt[x].end())
                ans += it->second;
            return;
        }
        if (x)
            back(x - 1, y, v);
        if (y)
            back(x, y - 1, v);
    };
    back(n - 1, n - 1, 0);
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

频次按相遇格区分；中心格不能重复异或两次；答案用六十四位。
