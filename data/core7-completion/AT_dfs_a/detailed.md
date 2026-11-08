## AT_dfs_a 深さ優先探索

原题：[AT_dfs_a](https://www.luogu.com.cn/problem/AT_dfs_a)

### 从问题到算法

把每个非墙格看成一个顶点，上下左右相邻的两格之间连边。题目只问是否存在路线，不需要求最短距离，因此按任意顺序遍历所有可达格即可。

先找到 s，把它放进栈并立即标记。取出一个格子时，检查四个相邻格；只有坐标合法、不是墙且未访问，才标记并入栈。在入栈时标记能避免多个邻居重复加入同一格。

每个加入栈的格子都有一条由起点延伸而来的路线；反过来，一条合法路线上的格子会依次被遍历。因此遍历结束后，g 被标记当且仅当起点能到达它。使用显式栈还避免了很长走廊造成递归栈溢出。

### 复杂度

时间 O(HW)，空间 O(HW)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int h, w;
    cin >> h >> w;
    vector<string> a(h);
    int start = -1, goal = -1;
    for (int i = 0; i < h; i++) {
        cin >> a[i];
        for (int j = 0; j < w; j++) {
            if (a[i][j] == 's')
                start = i * w + j;
            if (a[i][j] == 'g')
                goal = i * w + j;
        }
    }
    vector<char> seen(h * w);
    vector<int> st = {start};
    seen[start] = 1;
    int dx[] = {1, -1, 0, 0}, dy[] = {0, 0, 1, -1};
    while (!st.empty()) {
        int v = st.back();
        st.pop_back();
        int x = v / w, y = v % w;
        for (int k = 0; k < 4; k++) {
            int u = x + dx[k], v = y + dy[k];
            if (u >= 0 && u < h && v >= 0 && v < w && a[u][v] != '#' && !seen[u * w + v]) {
                seen[u * w + v] = 1;
                st.push_back(u * w + v);
            }
        }
    }
    cout << (seen[goal] ? "Yes" : "No") << '\n';

    return 0;
}
```

### 实现提醒

先判断坐标再访问数组；墙不能走；在入栈时标记。
