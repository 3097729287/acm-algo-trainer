## P1256 显示图像

原题：[P1256](https://www.luogu.com.cn/problem/P1256)

### 思路

把所有白色像素作为距离零的起点一起入队。四方向广搜中第一次到达一个格子时，就得到它到最近白点的曼哈顿距离。

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
