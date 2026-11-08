## P1355 神秘大三角

原题：[P1355](https://www.luogu.com.cn/problem/P1355)

### 思路

先判断是否与顶点重合，再判断是否在线段上。其它点若始终位于三条有向边的同一侧，就在三角形内部，否则在外部。

### 复杂度

时间 O(输入长度)，空间 O(输入长度)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Point {
    long long x, y;
};
long long cross(Point a, Point b, Point c) {
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string all, line;
    while (getline(cin, line))
        all += line + ' ';
    for (char &c : all)
        if (!isdigit((unsigned char)c) && c != '-')
            c = ' ';
    stringstream input(all);
    array<Point, 4> p;
    for (auto &v : p)
        input >> v.x >> v.y;
    Point q = p[3];
    for (int i = 0; i < 3; i++)
        if (p[i].x == q.x && p[i].y == q.y) {
            cout << 4 << '\n';
            return 0;
        }
    long long value[3];
    for (int i = 0; i < 3; i++) {
        auto a = p[i], b = p[(i + 1) % 3];
        value[i] = cross(a, b, q);
        if (value[i] == 0 && min(a.x, b.x) <= q.x && q.x <= max(a.x, b.x) && min(a.y, b.y) <= q.y &&
            q.y <= max(a.y, b.y)) {
            cout << 3 << '\n';
            return 0;
        }
    }
    bool inside = (value[0] > 0 && value[1] > 0 && value[2] > 0) ||
                  (value[0] < 0 && value[1] < 0 && value[2] < 0);
    cout << (inside ? 1 : 2) << '\n';

    return 0;
}
```

### 实现提醒

顶点先于边界判断；共线还要检查在线段范围；输出编号按题面。
