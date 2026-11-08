## P6566 观星

原题：[P6566](https://www.luogu.com.cn/problem/P6566)

### 思路

八方向搜索每个星座，得到它包含的星星数 s。令 count[s] 表示大小为 s 的星座个数，那么该星系大小为 s·count[s]。统计出现的 s 的数量及最大乘积。

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
