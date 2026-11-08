## CF1408F Two Different

原题：[CF1408F](https://www.luogu.com.cn/problem/CF1408F)

### 思路

取不超过 n 的最大二次幂 L，对前 L 个、后 L 个位置分别进行分治配对。二次幂区间能变成同一个表达式；第二次覆盖后，全数组最多保留两种值。

### 复杂度

时间与输出 O(n log n)，递归空间 O(log n)，保存操作 O(n log n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    int L = 1;
    while (2 * L <= n)
        L *= 2;
    vector<pair<int, int>> ops;
    function<void(int, int)> solve = [&](int l, int length) {
        if (length == 1)
            return;
        int half = length / 2;
        solve(l, half);
        solve(l + half, half);
        for (int i = 0; i < half; i++)
            ops.push_back({l + i, l + half + i});
    };
    solve(1, L);
    solve(n - L + 1, L);
    cout << ops.size() << '\n';
    for (auto [a, b] : ops)
        cout << a << ' ' << b << '\n';

    return 0;
}
```

### 实现提醒

函数可能不交换，配对方向保持一致；两段允许重叠；先分后合。
