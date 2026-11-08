## AT_dfs_a 深さ優先探索

原题：[AT_dfs_a](https://www.luogu.com.cn/problem/AT_dfs_a)

### 思路

从起点出发，只走未访问的非墙格，把能到达的格子全部标记。终点被标记就输出 Yes，否则输出 No。

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
