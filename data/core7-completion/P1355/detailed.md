## P1355 神秘大三角

原题：[P1355](https://www.luogu.com.cn/problem/P1355)

### 从问题到算法

有向边 A→B 与向量 A→P 的叉积，正负表示 P 在边的左侧或右侧，零表示共线。按三角形顶点顺序，内部点必须对三条边都在同一侧；顶点为顺时针或逆时针都能用“全正或全负”判断。

边界情况要先处理。点与任一顶点坐标相等，输出四。叉积为零还不够，因为点可能落在边的延长线上；同时要求横纵坐标均在两端的闭范围内，才在线段上，输出三。

剩余点的三个叉积若全正或全负输出一，否则输出二。输入坐标带括号和逗号，先把非数字且非负号字符替换为空格，再按整数读入。

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
