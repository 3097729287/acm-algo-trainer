## P11380 排队

原题：[P11380](https://www.luogu.com.cn/problem/P11380)

### 从问题到算法

约束 a 紧挨着 b 前面，意味着 next[a]=b 且 previous[b]=a。某人若被要求接两个不同后继或前驱，无法同时满足；重复的同一条约束则没有新增限制。

没有冲突时，每个点入度、出度至多一，连通结构只能是定向链或定向环。环不可能放到一条直线队伍中。从所有没有前驱的人出发沿后继遍历，若未覆盖全部人，就说明剩余结构中存在环。

合法时，每条链的内部次序被完全确定，且不能在中间插入其它人，否则破坏相邻关系。不同链之间没有约束，所以把链作为整体排列，有 K! 种。单独一个人也算一条链。

### 复杂度

时间 O(n+m)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<int> next(n + 1), previous(n + 1);
    bool ok = true;
    while (m--) {
        int a, b;
        cin >> a >> b;
        if (a == b || (next[a] && next[a] != b) || (previous[b] && previous[b] != a))
            ok = false;
        else {
            next[a] = b;
            previous[b] = a;
        }
    }
    int chains = 0, visited = 0;
    for (int i = 1; i <= n; i++)
        if (!previous[i]) {
            chains++;
            for (int v = i; v; v = next[v])
                visited++;
        }
    if (!ok || visited != n) {
        cout << 0 << '\n';
        return 0;
    }
    long long ans = 1;
    for (int i = 1; i <= chains; i++)
        ans = ans * i % 1000000007;
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

重复约束不重复计数；自环无解；检查所有点是否属于某条链。
