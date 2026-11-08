## P1443 马的遍历

原题：[P1443](https://www.luogu.com.cn/problem/P1443)

### 从问题到算法

从起点走一步能到的格子距离是 1，再从这些格子走一步，才可能得到距离为 2 的新格子。这种逐层扩展正是广度优先搜索。

距离数组初始为 -1，起点置 0 并入队。每次取出队首，枚举横向 1、纵向 2 或横向 2、纵向 1 的八种带符号位移；合法且距离仍为 -1 的格子得到当前距离加 1，再加入队尾。

队列中的距离单调不降。假设第一次到某格的路线不是最短路线，那么更短路线的倒数第二格会先出队，并且更早发现它，产生矛盾。无须重复松弛。输出按题目要求使用左对齐固定列宽，-1 表示不可达。

### 复杂度

时间 O(nm)，空间 O(nm)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, x, y;
    cin >> n >> m >> x >> y;
    x--;
    y--;
    vector<vector<int>> d(n, vector<int>(m, -1));
    queue<pair<int, int>> q;
    q.push({x, y});
    d[x][y] = 0;
    int dx[] = {1, 1, -1, -1, 2, 2, -2, -2}, dy[] = {2, -2, 2, -2, 1, -1, 1, -1};
    while (!q.empty()) {
        auto [a, b] = q.front();
        q.pop();
        for (int k = 0; k < 8; k++) {
            int u = a + dx[k], v = b + dy[k];
            if (u >= 0 && u < n && v >= 0 && v < m && d[u][v] < 0) {
                d[u][v] = d[a][b] + 1;
                q.push({u, v});
            }
        }
    }
    for (auto &row : d) {
        for (int value : row)
            cout << left << setw(5) << value;
        cout << '\n';
    }

    return 0;
}
```

### 实现提醒

输入坐标是 1 起始；八种位移不能漏；不要把未访问初始化成 0。
