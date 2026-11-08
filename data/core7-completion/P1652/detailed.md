## P1652 圆

原题：[P1652](https://www.luogu.com.cn/problem/P1652)

### 从问题到算法

圆周把平面分成内部与外部。若两点分处两侧，连续曲线必须跨过边界，至少一次；若在同侧，这个圆本身不强制跨越。

题目保证各圆互不相交也不相切，它们只能分离或相互包含，因此这些圆周形成无交叉的层次边界。可以沿圆形成的区域层次从起点所在区域走到终点区域，恰好跨过内外状态不同的那些圆，达到上述下界。

判断是否在内部只比较距离平方与半径平方，无需开方。输入的所有 x、所有 y、所有 r 分三行给出，不能错读成逐圆的三元组。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> x(n), y(n), r(n);
    for (auto &v : x)
        cin >> v;
    for (auto &v : y)
        cin >> v;
    for (auto &v : r)
        cin >> v;
    long long x1, y1, x2, y2;
    cin >> x1 >> y1 >> x2 >> y2;
    int ans = 0;
    for (int i = 0; i < n; i++) {
        bool a = (x1 - x[i]) * (x1 - x[i]) + (y1 - y[i]) * (y1 - y[i]) < r[i] * r[i];
        bool b = (x2 - x[i]) * (x2 - x[i]) + (y2 - y[i]) * (y2 - y[i]) < r[i] * r[i];
        ans += a != b;
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

圆参数按三组数组读取；用平方比较；起终点保证不在圆周上。
