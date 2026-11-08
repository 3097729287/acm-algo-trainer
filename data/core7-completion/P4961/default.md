## P4961 小埋与扫雷

原题：[P4961](https://www.luogu.com.cn/problem/P4961)

### 思路

先计算每个非雷格周围雷数。每个八连通零格块只需点一次，并会自动展开周围数字；最后仍未展开的非雷数字格各需再点一次。

### 复杂度

时间 O(nm)，空间 O(nm)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<vector<int>> a(n, vector<int>(m)), near = a;
    for (auto &row : a)
        for (int &x : row)
            cin >> x;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++)
            for (int dx = -1; dx <= 1; dx++)
                for (int dy = -1; dy <= 1; dy++) {
                    int x = i + dx, y = j + dy;
                    if (x >= 0 && x < n && y >= 0 && y < m)
                        near[i][j] += a[x][y];
                }
    vector<vector<char>> seen(n, vector<char>(m));
    int ans = 0;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++)
            if (!a[i][j] && !near[i][j] && !seen[i][j]) {
                ans++;
                queue<pair<int, int>> q;
                q.push({i, j});
                seen[i][j] = 1;
                while (!q.empty()) {
                    auto [x, y] = q.front();
                    q.pop();
                    for (int dx = -1; dx <= 1; dx++)
                        for (int dy = -1; dy <= 1; dy++) {
                            int u = x + dx, v = y + dy;
                            if (u >= 0 && u < n && v >= 0 && v < m && !a[u][v] && !seen[u][v]) {
                                seen[u][v] = 1;
                                if (!near[u][v])
                                    q.push({u, v});
                            }
                        }
                }
            }
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++)
            if (!a[i][j] && !seen[i][j])
                ans++;
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

使用八邻域；数字只标记，不继续入队扩张；雷格始终不点击。
