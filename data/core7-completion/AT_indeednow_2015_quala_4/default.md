## AT_indeednow_2015_quala_4 パズル

原题：[AT_indeednow_2015_quala_4](https://www.luogu.com.cn/problem/AT_indeednow_2015_quala_4)

### 思路

所有非空格到目标位置的曼哈顿距离之和是剩余步数下界。逐渐增加允许总步数，深搜中若已走步数加这个下界超限就剪枝，并跳过立即撤销上一步的移动。

### 复杂度

最坏指数时间，实际搜索由深度二十四保证和曼哈顿剪枝控制；递归空间 O(24+HW)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int h, w;
    cin >> h >> w;
    int n = h * w;
    vector<int> a(n);
    int blank = 0, estimate = 0;
    vector<vector<int>> distance(n, vector<int>(n));
    for (int p = 0; p < n; p++)
        for (int value = 1; value < n; value++)
            distance[p][value] = abs(p / w - (value - 1) / w) + abs(p % w - (value - 1) % w);
    for (int i = 0; i < n; i++) {
        cin >> a[i];
        if (a[i])
            estimate += distance[i][a[i]];
        else
            blank = i;
    }
    vector<vector<int>> neighbors(n);
    for (int p = 0; p < n; p++)
        for (auto [dx, dy] : vector<pair<int, int>>{{1, 0}, {-1, 0}, {0, 1}, {0, -1}}) {
            int x = p / w + dx, y = p % w + dy;
            if (x >= 0 && x < h && y >= 0 && y < w)
                neighbors[p].push_back(x * w + y);
        }
    function<bool(int, int, int, int, int)> search = [&](int hole, int previous, int used,
                                                         int lower, int limit) {
        if (used + lower > limit)
            return false;
        if (lower == 0)
            return true;
        vector<pair<int, int>> moves;
        for (int next : neighbors[hole])
            if (next != previous) {
                int value = a[next],
                    newLower = lower - distance[next][value] + distance[hole][value];
                moves.push_back({newLower, next});
            }
        sort(moves.begin(), moves.end());
        for (auto [newLower, next] : moves) {
            swap(a[hole], a[next]);
            bool found = search(next, hole, used + 1, newLower, limit);
            swap(a[hole], a[next]);
            if (found)
                return true;
        }
        return false;
    };
    for (int limit = estimate; limit <= 24; limit += 2)
        if (search(blank, -1, 0, estimate, limit)) {
            cout << limit << '\n';
            return 0;
        }

    return 0;
}
```

### 实现提醒

不计算空格的曼哈顿距离；交换后回溯恢复；棋盘可达六乘六；只跳过直接回退。
