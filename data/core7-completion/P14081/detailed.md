## P14081 炸弹游戏

原题：[P14081](https://www.luogu.com.cn/problem/P14081)

### 从问题到算法

炸弹只能放在不相邻的点上，花火能否放 m 个炸弹就是图是否存在大小至少 m 的独立集。首先简单图最多有 n(n−1)/2 条边，故 n 不能小于容量下界 L。

若 m 条边不是两两不相交，就有两条共享一个端点，选这个端点并对其余每边选一个端点，可用至多 m−1 个点覆盖所有边，其余至少 n−m+1 个点构成独立集。若边两两不相交，则至少需要 2m 个顶点，独立集更不可能小于 m。因此 n≥2m−1 时必输。

当 m≥3，三角形加 m−3 条独立边、再加一个孤立点，共 2m−2 点、m 边，最大独立集恰有 m−1 点，可以获胜。对任何 L<=n<=2m−2，删去多余顶点，再补边至 m 条，不会增大独立集；容量条件保证能补足。二分最小 L，右界取 2m−2，比较两者即可。

### 复杂度

每组时间 O(log m)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        long long m;
        cin >> m;
        long long l = 1, r = 2 * m;
        while (l < r) {
            long long mid = (l + r) / 2;
            if (mid * (mid - 1) / 2 >= m)
                r = mid;
            else
                l = mid + 1;
        }
        long long high = 2 * m - 2;
        if (l > high)
            cout << "Lose!\n";
        else
            cout << l << ' ' << high << '\n';
    }

    return 0;
}
```

### 实现提醒

不允许重边与自环；m=1、2 由边界比较自然判输；容量乘积用六十四位。
