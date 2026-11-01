## I. Ice Skating

### 题意

有最多 $100$ 个整数坐标雪堆，只能沿横向或纵向滑到其他雪堆。求最少新增几堆，才能使所有雪堆互相可达。

### 从零讲：queue 的基本用法

**队列 `std::queue`。** 队列先进先出：`q.push(v);` 在尾部加入，`q.front();` 读取头部，`q.pop();` 移除头部且不返回元素。`q.front();`、`q.pop();` 都要求队列非空，所以外层先检查 `q.empty();`。这些操作均为 $O(1)$；BFS 把已经发现的点入队、入队时标记，避免重复扩展。

### 思路

将同横坐标或同纵坐标的雪堆连边，统计连通块数 $c$，答案为 $c-1$。

![用一个交点雪堆连接两块](assets/i-bridge.svg)

上界：从两块中各选一点 $(x_1,y_1)$、$(x_2,y_2)$，在 $(x_1,y_2)$ 加一堆即可合并。下界：新点所在行中的旧雪堆本就相互连通，列中的也一样，所以一次最多合并两块，块数最多减少一。不断合并正好需要 $c-1$ 堆。用 BFS 扫描同一行或列的点，时间 $O(n^2)$，空间 $O(n)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<int> x(n), y(n);
    for (int i = 0; i < n; ++i) cin >> x[i] >> y[i];
    vector<bool> seen(n, false);
    int components = 0;
    for (int s = 0; s < n; ++s) {
        if (seen[s]) continue;
        ++components;
        queue<int> q;
        q.push(s);
        seen[s] = true;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            for (int v = 0; v < n; ++v) {
                if (!seen[v] && (x[u] == x[v] || y[u] == y[v])) {
                    seen[v] = true;  // 入队时标记，避免重复加入。
                    q.push(v);
                }
            }
        }
    }
    cout << components - 1 << '\n';
}
```

### 易错点

同一行或列不必相邻编号；原本只有一个连通块时答案为零。
