## P1265 公路修建

原题：[P1265](https://www.luogu.com.cn/problem/P1265)

### 从问题到算法

完整图有平方数量的边，把它们全部存下并排序没有必要。Prim 每次只需要知道每个未选点到已选集合的最短连接距离。

初始任选一个城镇，距离为零。每轮扫描所有未选点，挑连接距离最小者加入，费用累加它的距离；再用新点到其它未选点的直线距离更新记录。这个选择始终是跨越“已选与未选”割的最小边，满足最小生成树割性质。

比较时可以保存距离平方，只在实际加入点时开平方累加，从而减少开方调用。总共 n 轮，每轮线性扫描，空间仅为坐标、距离和选中标记。

### 复杂度

时间 O(n²)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long double> x(n), y(n), distance(n, numeric_limits<long double>::infinity());
    for (int i = 0; i < n; i++)
        cin >> x[i] >> y[i];
    vector<char> used(n);
    distance[0] = 0;
    long double ans = 0;
    for (int step = 0; step < n; step++) {
        int v = -1;
        for (int i = 0; i < n; i++)
            if (!used[i] && (v < 0 || distance[i] < distance[v]))
                v = i;
        used[v] = 1;
        ans += sqrt(distance[v]);
        for (int u = 0; u < n; u++)
            if (!used[u])
                distance[u] =
                    min(distance[u], (x[u] - x[v]) * (x[u] - x[v]) + (y[u] - y[v]) * (y[u] - y[v]));
    }
    cout << fixed << setprecision(2) << ans << '\n';

    return 0;
}
```

### 实现提醒

距离比较可用平方；加入时才开方；答案保留两位小数。
