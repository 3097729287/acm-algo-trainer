## P1883 三分 / 函数 / [ICPC 2010 Chengdu R] Error Curves

原题：[P1883](https://www.luogu.com.cn/problem/P1883)

### 从问题到算法

题目要求最小化所有函数中的最大值。设 F(x)=max fi(x)，不能分别求各函数的最小值后再取最大，因为它们可能在不同位置达到最小。

每个 fi 是凸函数；对任意两点及其中间点，各 fi 都不超过端点值的同权加权和，再取最大仍保留凸性。因此 F 在区间上是单谷的，可以用三分比较 m1、m2 处的值。若 F(m1)<F(m2)，最优点不会在 m2 右侧，否则对称舍掉左侧。

固定迭代一百次足以使区间误差远小于输出要求。每次评估遍历全部函数，用 double，并最终输出剩余区间中点处的 F。

### 复杂度

时间 O(T·n·迭代次数)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        int n;
        cin >> n;
        vector<array<double, 3>> a(n);
        for (auto &v : a)
            cin >> v[0] >> v[1] >> v[2];
        auto value = [&](double x) {
            double answer = -1e100;
            for (auto v : a)
                answer = max(answer, (v[0] * x + v[1]) * x + v[2]);
            return answer;
        };
        double l = 0, r = 1000;
        for (int i = 0; i < 120; i++) {
            double x = (2 * l + r) / 3, y = (l + 2 * r) / 3;
            if (value(x) < value(y))
                r = y;
            else
                l = x;
        }
        cout << fixed << setprecision(4) << value((l + r) / 2) << '\n';
    }

    return 0;
}
```

### 实现提醒

评估的是所有二次函数的最大值；搜索区间 [0,1000]；输出四位小数。
