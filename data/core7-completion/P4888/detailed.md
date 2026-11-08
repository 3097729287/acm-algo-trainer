## P4888 三去矩阵

原题：[P4888](https://www.luogu.com.cn/problem/P4888)

### 从问题到算法

题目只问给定格子为中心的回文，不要求预处理全部中心。中心是一个实际格子，所以所有合法回文长度都是奇数，初始长度为一。

沿水平方向比较左右距离一的两格，再比较距离二，直到越界或不相同为止。由于更长回文必须包含更短回文，第一次失败后不可能再有更大半径。竖直方向完全相同。

每次最多检查矩阵边长的常数倍，边长和询问数都不超过两千，总比较次数只有几百万，直接扩展已经足够。这样实现比为所有行列建立哈希更简单，且没有碰撞。

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
