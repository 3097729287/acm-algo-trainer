## P2324 骑士精神

原题：[P2324](https://www.luogu.com.cn/problem/P2324)

### 从问题到算法

每次只移动一个非空棋子，因此最多修正一个错位棋子；错位非空棋子数 h 不会大于真正剩余步数，是可用的剪枝下界。空格不计入 h，避免一次交换被错误地当成需要两步。

对限制 limit 进行深搜，若 used+h>limit 立即返回。交换时只更新被移动棋子的错位贡献；回溯时恢复棋盘。限制从 h 开始递增，第一次找到目标的限制即为最短解。

马步会改变空格的棋盘颜色，所以解长奇偶等于初始空格到中心的颜色差，可只枚举对应奇偶的 limit。禁止立即退回上一步可以去掉无用往返，不会删掉任何最短解。十五步仍找不到时输出 −1。

### 复杂度

最坏指数时间，深度最多十五且使用可采纳下界剪枝；空间 O(25+15)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    string goal = "111110111100*110000100000";
    while (T--) {
        string a;
        for (int i = 0; i < 5; i++) {
            string row;
            cin >> row;
            a += row;
        }
        int hole = a.find('*'), h = 0;
        for (int i = 0; i < 25; i++)
            if (a[i] != '*' && a[i] != goal[i])
                h++;
        vector<vector<int>> g(25);
        for (int i = 0; i < 25; i++)
            for (auto [dx, dy] : vector<pair<int, int>>{
                     {1, 2}, {1, -2}, {-1, 2}, {-1, -2}, {2, 1}, {2, -1}, {-2, 1}, {-2, -1}}) {
                int x = i / 5 + dx, y = i % 5 + dy;
                if (x >= 0 && x < 5 && y >= 0 && y < 5)
                    g[i].push_back(x * 5 + y);
            }
        function<bool(int, int, int, int, int)> dfs = [&](int p, int prev, int used, int lower,
                                                          int limit) {
            if (used + lower > limit)
                return false;
            if (a == goal)
                return true;
            if (used == limit)
                return false;
            vector<pair<int, int>> moves;
            for (int u : g[p])
                if (u != prev)
                    moves.push_back({lower - (a[u] != goal[u]) + (a[u] != goal[p]), u});
            sort(moves.begin(), moves.end());
            for (auto [nh, u] : moves) {
                swap(a[p], a[u]);
                bool found = dfs(u, p, used + 1, nh, limit);
                swap(a[p], a[u]);
                if (found)
                    return true;
            }
            return false;
        };
        int parity = (hole / 5 + hole % 5) % 2, ans = -1;
        for (int limit = h; limit <= 15; limit++)
            if (limit % 2 == parity && dfs(hole, -1, 0, h, limit)) {
                ans = limit;
                break;
            }
        cout << ans << '\n';
    }

    return 0;
}
```

### 实现提醒

下界不计空格；每次交换后恢复；目标中心为 *。
