## CF771C Bear and Tree Jumps

原题：[CF771C](https://www.luogu.com.cn/problem/CF771C)

### 思路

跳跃数为 ceil(dist/k)。先用边贡献统计所有点对距离，再用子树 DP 统计距离模 k 时需补到下一个 k 倍数的数量，最后总和除以 k。

### 复杂度

时间 O(nk²)，空间 O(nk)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    cin >> n >> k;
    vector<vector<int>> g(n);
    for (int i = 1; i < n; i++) {
        int a, b;
        cin >> a >> b;
        a--;
        b--;
        g[a].push_back(b);
        g[b].push_back(a);
    }
    vector<int> parent(n, -1), order = {0}, size(n, 1);
    parent[0] = 0;
    for (int i = 0; i < n; i++)
        for (int u : g[order[i]])
            if (parent[u] < 0) {
                parent[u] = order[i];
                order.push_back(u);
            }
    vector<array<long long, 5>> cnt(n);
    long long distanceSum = 0, padding = 0;
    for (int i = n - 1; i >= 0; i--) {
        int v = order[i];
        cnt[v][0] = 1;
        for (int u : g[v])
            if (parent[u] == v) {
                for (int a = 0; a < k; a++)
                    for (int b = 0; b < k; b++)
                        padding += cnt[v][a] * cnt[u][b] * ((k - (a + b + 1) % k) % k);
                for (int b = 0; b < k; b++)
                    cnt[v][(b + 1) % k] += cnt[u][b];
                size[v] += size[u];
            }
        if (v)
            distanceSum += 1LL * size[v] * (n - size[v]);
    }
    cout << (distanceSum + padding) / k << '\n';

    return 0;
}
```

### 实现提醒

点对无序，只合并不同已处理分支；余数零无需补；最终总和整除 k。
