## P4961 小埋与扫雷

原题：[P4961](https://www.luogu.com.cn/problem/P4961)

### 从问题到算法

没有邻雷的空格被点开后，会自动展开相邻空格及其周围数字，因此整个八连通空格块只需一次点击。不同空格块无法互相展开，至少各点一次，这给出了必要点击数。

先统计八邻域雷数。遇到尚未访问的零格时，答案加一，BFS 遍历这个零块，并把它周围所有非雷格标为已展开；只把零格加入队列，数字格不能继续扩张。

完成全部零块后，尚未展开的非雷格都不与任何零格相邻，无法借助自动展开，只能逐个点击。因此各加一，得到下界可实现的最少次数。

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
