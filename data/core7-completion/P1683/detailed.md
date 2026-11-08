## P1683 入门

原题：[P1683](https://www.luogu.com.cn/problem/P1683)

### 从问题到算法

题目允许重复走同一块瓷砖，因此不需要求最长简单路径。只要格子与入口在同一个安全连通块中，就可以通过来回行走到达它。

找到 @ 后入队并标记，每次取出一个格子计数，再把四邻中尚未访问的安全格入队。搜索结束时，这个连通块中的全部格子都已计算，障碍或其它安全块都不会被计入。输入先给宽 W 再给高 H，接下来读 H 行。

### 复杂度

时间 O(WH)，空间 O(WH)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int w, h;
    cin >> w >> h;
    vector<string> a(h);
    queue<pair<int, int>> q;
    for (int i = 0; i < h; i++) {
        cin >> a[i];
        for (int j = 0; j < w; j++)
            if (a[i][j] == '@') {
                q.push({i, j});
                a[i][j] = '#';
            }
    }
    int ans = 0;
    int dx[4] = {1, -1, 0, 0}, dy[4] = {0, 0, 1, -1};
    while (!q.empty()) {
        auto [x, y] = q.front();
        q.pop();
        ans++;
        for (int d = 0; d < 4; d++) {
            int nx = x + dx[d], ny = y + dy[d];
            if (nx >= 0 && nx < h && ny >= 0 && ny < w && a[nx][ny] == '.') {
                a[nx][ny] = '#';
                q.push({nx, ny});
            }
        }
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

入口本身也计数；输入是宽、高；不能斜走。
