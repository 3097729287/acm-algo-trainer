## P1451 求细胞数量

原题：[P1451](https://www.luogu.com.cn/problem/P1451)

### 思路

每次找到尚未访问的非零格，就发现一个新细胞。用队列把与它四方向连通的所有非零格标记，最后统计启动搜索的次数。

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
