## AT_abc271_f XOR on Grid Path

原题：[AT_abc271_f](https://www.luogu.com.cn/problem/AT_abc271_f)

### 从问题到算法

完整路径长二 n 减二，直接枚举有接近四的 n 次方种可能。所有完整路径都会恰好经过一个 i+j=n−1 的格子，可以在这里分成两半，每半最多二的 n−1 次方条路径。

前半异或 A、后半异或 B 都包含中心格的值 x，所以整条路径异或为 A xor B xor x。要使它为零，需要 A=B xor x。为每个中心格分别记录前半异或频次，反向枚举后半时查对应频次并相加。

每条路径由两半唯一确定，查表不会重复计数。路径数量可能超过三十二位，频次和答案使用 long long。

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
