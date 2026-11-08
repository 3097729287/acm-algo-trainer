## P6566 观星

原题：[P6566](https://www.luogu.com.cn/problem/P6566)

### 从问题到算法

星座由位置连接决定，星系由星座大小决定，这两个步骤必须分别处理。先对所有 * 做八方向连通块搜索，每个块的格子数就是星座大小。

得到一个大小 s 后令 count[s] 加一。大小相同但位置不同的星座属于同一星系，因此这个星系共含 s·count[s] 颗星；不同的 s 对应不同星系。遍历计数表，非零项数是星系数，最大乘积是最大星系大小。没有星星时两者都是零。

矩阵可达一千五百行，使用显式队列，避免递归深度随星座大小增长。

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
    vector<string> a(n);
    for (auto &s : a)
        cin >> s;
    vector<int> cnt(n * m + 1);
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++)
            if (a[i][j] == '*') {
                vector<int> q = {i * m + j};
                a[i][j] = '.';
                for (int k = 0; k < (int)q.size(); k++) {
                    int x = q[k] / m, y = q[k] % m;
                    for (int dx = -1; dx <= 1; dx++)
                        for (int dy = -1; dy <= 1; dy++) {
                            int nx = x + dx, ny = y + dy;
                            if (nx >= 0 && nx < n && ny >= 0 && ny < m && a[nx][ny] == '*') {
                                a[nx][ny] = '.';
                                q.push_back(nx * m + ny);
                            }
                        }
                }
                cnt[q.size()]++;
            }
    int systems = 0, best = 0;
    for (int s = 1; s <= n * m; s++)
        if (cnt[s]) {
            systems++;
            best = max(best, s * cnt[s]);
        }
    cout << systems << ' ' << best << '\n';

    return 0;
}
```

### 实现提醒

相邻有八方向；最大的是星系总星数，不是单个星座大小；计数表按大小归类。
