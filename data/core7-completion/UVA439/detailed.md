## UVA439 骑士的移动 Knight Moves

原题：[UVA439](https://www.luogu.com.cn/problem/UVA439)

### 从问题到算法

每次移动的代价都为一步，因此不能按几何直线距离估算，而要在棋盘允许的边上求最短路。横坐标由字母减 a 得到，纵坐标由数字减 1 得到。

为每组起终点重新建立距离数组，只把起点置为 0。队列逐层扩展，八种马步均检查是否仍在棋盘内。第一次访问某格时记录当前格距离加 1；后来的路线不可能更短，所以不再入队。起终点相同时自然得到 0。

输入直到文件结束，多组之间不能复用旧距离。最后保留题目规定的整句输出和标点。

### 复杂度

每组时间 O(64)，空间 O(64)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string a, b;
    while (cin >> a >> b) {
        int d[8][8];
        memset(d, -1, sizeof d);
        queue<pair<int, int>> q;
        int sx = a[0] - 'a', sy = a[1] - '1';
        d[sx][sy] = 0;
        q.push({sx, sy});
        int dx[] = {1, 1, -1, -1, 2, 2, -2, -2}, dy[] = {2, -2, 2, -2, 1, -1, 1, -1};
        while (!q.empty()) {
            auto [x, y] = q.front();
            q.pop();
            for (int k = 0; k < 8; k++) {
                int u = x + dx[k], v = y + dy[k];
                if (u >= 0 && u < 8 && v >= 0 && v < 8 && d[u][v] < 0) {
                    d[u][v] = d[x][y] + 1;
                    q.push({u, v});
                }
            }
        }
        cout << "To get from " << a << " to " << b << " takes " << d[b[0] - 'a'][b[1] - '1']
             << " knight moves.\n";
    }

    return 0;
}
```

### 实现提醒

读到 EOF；保留原坐标字符串用于输出；每组清空距离。
