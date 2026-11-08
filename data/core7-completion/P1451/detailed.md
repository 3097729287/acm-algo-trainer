## P1451 求细胞数量

原题：[P1451](https://www.luogu.com.cn/problem/P1451)

### 从问题到算法

数字的具体大小不影响连接，只有零与非零的区别。按行列扫描，每遇到未标记的非零格，答案加一，从它开始广搜。

搜索只走上下左右四个方向，不能走对角线；发现新格时立即标记，避免重复入队。一次搜索恰好遍历一个连通块，扫描会为每个块启动且仅启动一次，所以启动次数就是细胞数量。

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
    vector<string> a(n);
    for (auto &s : a)
        cin >> s;
    int ans = 0;
    int dx[4] = {1, -1, 0, 0}, dy[4] = {0, 0, 1, -1};
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++)
            if (a[i][j] != '0') {
                ans++;
                queue<pair<int, int>> q;
                q.push({i, j});
                a[i][j] = '0';
                while (!q.empty()) {
                    auto [x, y] = q.front();
                    q.pop();
                    for (int d = 0; d < 4; d++) {
                        int nx = x + dx[d], ny = y + dy[d];
                        if (nx >= 0 && nx < n && ny >= 0 && ny < m && a[nx][ny] != '0') {
                            a[nx][ny] = '0';
                            q.push({nx, ny});
                        }
                    }
                }
            }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

字符零是 '0'；只走四方向；入队时标记。
