## P4888 三去矩阵

原题：[P4888](https://www.luogu.com.cn/problem/P4888)

### 思路

每次询问分别沿所在行和列向两侧同步扩展，只要两侧字母相同就继续。中心固定为一个格子，因此只需检查奇数长度回文，取水平和竖直的最大值。

### 复杂度

每次 O(l)，总时间 O(l²+ql)，空间 O(l²)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<string> a(n);
    for (auto &s : a)
        cin >> s;
    while (q--) {
        int x, y;
        cin >> x >> y;
        x--;
        y--;
        int horizontal = 0, vertical = 0;
        while (y - horizontal - 1 >= 0 && y + horizontal + 1 < n &&
               a[x][y - horizontal - 1] == a[x][y + horizontal + 1])
            horizontal++;
        while (x - vertical - 1 >= 0 && x + vertical + 1 < n &&
               a[x - vertical - 1][y] == a[x + vertical + 1][y])
            vertical++;
        cout << 2 * max(horizontal, vertical) + 1 << '\n';
    }

    return 0;
}
```

### 实现提醒

坐标转为 0 起始；只取水平或竖直，不能走对角线；中心本身长度为 1。
