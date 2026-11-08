## CF1408F Two Different

原题：[CF1408F](https://www.luogu.com.cn/problem/CF1408F)

### 从问题到算法

长度二的区间直接配对后相等。归纳地，先把左右半区各处理成一致值 A、B，再将对应位置按同样方向逐对操作，每对都变成 f(A,B)，所以整个区间一致，不要求 f 有任何交换或结合性质。

L 是最大二次幂，有 2L≥n。先处理前 L 个使它们成为 A，再处理后 L 个成为 B。第二次操作之后，后 L 个全为 B，前面未被覆盖的部分仍全为 A，故至多两值。重叠部分旧值如何并不影响第二次分治的归纳结论。

每段操作数为 (L/2)log2 L，两段总计 Llog2 L，远低于五十万。输出顺序要先递归两半，再逐对归并，不能倒过来。

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
