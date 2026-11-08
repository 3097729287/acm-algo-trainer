## P1256 显示图像

原题：[P1256](https://www.luogu.com.cn/problem/P1256)

### 从问题到算法

单个白点到任意格子的最短四方向步数等于曼哈顿距离。若分别为每个黑点搜索，会重复遍历大量格子；将所有白点放在同一个队列中，相当于让距离一、二、三的波前同时扩展。

所有起点距离设零，其余设为未访问。每次从距离 d 的格子扩展到未访问邻居，令其距离为 d+1。BFS 按距离非降序处理，因此不存在另一个白点能在首次赋值之后提供更短路线。

### 复杂度

时间 O(NM)，空间 O(NM)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<vector<int>> d(n, vector<int>(m, -1));
    queue<pair<int, int>> q;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++) {
            char c;
            cin >> c;
            if (c == '1') {
                d[i][j] = 0;
                q.push({i, j});
            }
        }
    int dx[4] = {1, -1, 0, 0}, dy[4] = {0, 0, 1, -1};
    while (!q.empty()) {
        auto [x, y] = q.front();
        q.pop();
        for (int k = 0; k < 4; k++) {
            int nx = x + dx[k], ny = y + dy[k];
            if (nx >= 0 && nx < n && ny >= 0 && ny < m && d[nx][ny] < 0) {
                d[nx][ny] = d[x][y] + 1;
                q.push({nx, ny});
            }
        }
    }
    for (auto &r : d) {
        for (int j = 0; j < m; j++)
            cout << r[j] << (j + 1 == m ? '\n' : ' ');
    }

    return 0;
}
```

### 实现提醒

所有白点必须先入队；白点自身输出零；入队时赋距离。
