## AT_indeednow_2015_quala_4 パズル

原题：[AT_indeednow_2015_quala_4](https://www.luogu.com.cn/problem/AT_indeednow_2015_quala_4)

### 从问题到算法

一次操作只把一个数字格移动一格，它到目标的曼哈顿距离至多减少一。因此所有数字格距离之和 h 不会高估还需的操作数，是安全的搜索下界；空白格不计入。

从初始 h 开始限制总步数，只有当前步数 g+h 不超过限制的分支才继续。每移动一个数字，只更新这个数字的距离变化，不必重算整个棋盘。数字按目标行列确定位置，适用于六乘六而非只能编码十五数码。

一次移动使 h 的奇偶翻转，因此解长与初始 h 同奇偶，限制每次增加二即可。优先尝试使 h 较小的移动，找解更快；禁止空白立即走回原位置，去掉必无价值的往返。原题保证最短解不超过二十四，首次找到的迭代深度就是最短步数。

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
