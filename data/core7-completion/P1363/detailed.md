## P1363 幻象迷宫

原题：[P1363](https://www.luogu.com.cn/problem/P1363)

### 从问题到算法

只记录行列取模后的访问状态会漏掉跨周期移动。为每个周期格记录首次到达的真实整数坐标，扩展时真实坐标加方向，再用规范化取模判断对应格是否为墙。

如果新坐标与某格保存的真实坐标不同，两者相差一个非零周期平移。连接这两种到达方式得到一条跨周期路线；地图周期重复，这条路线可以平移后不断重走，于是能够走到无限远。

反之，如果每个周期格始终只有同一个真实坐标可达，实际可达位置最多 nm 个，无法无限走远。因此发现这种冲突就输出 Yes，全部搜索完仍无冲突则输出 No。多组地图读到文件结束。

### 复杂度

每组时间 O(nm)，空间 O(nm)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    while (cin >> n >> m) {
        vector<string> a(n);
        pair<int, int> start;
        for (int i = 0; i < n; i++) {
            cin >> a[i];
            for (int j = 0; j < m; j++)
                if (a[i][j] == 'S')
                    start = {i, j};
        }
        vector<char> seen(n * m);
        vector<pair<int, int>> first(n * m);
        queue<pair<int, int>> q;
        q.push(start);
        seen[start.first * m + start.second] = 1;
        first[start.first * m + start.second] = start;
        bool yes = false;
        int dx[4] = {1, -1, 0, 0}, dy[4] = {0, 0, 1, -1};
        while (!q.empty() && !yes) {
            auto [x, y] = q.front();
            q.pop();
            for (int d = 0; d < 4; d++) {
                int nx = x + dx[d], ny = y + dy[d], r = (nx % n + n) % n, c = (ny % m + m) % m,
                    id = r * m + c;
                if (a[r][c] == '#')
                    continue;
                if (seen[id]) {
                    if (first[id] != pair<int, int>{nx, ny}) {
                        yes = true;
                        break;
                    }
                } else {
                    seen[id] = 1;
                    first[id] = {nx, ny};
                    q.push({nx, ny});
                }
            }
        }
        cout << (yes ? "Yes" : "No") << '\n';
    }

    return 0;
}
```

### 实现提醒

负坐标的余数要规范化；比较真实坐标；输入直到 EOF。
