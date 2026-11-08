## P1883 三分 / 函数 / [ICPC 2010 Chengdu R] Error Curves

原题：[P1883](https://www.luogu.com.cn/problem/P1883)

### 思路

每个二次函数在定义区间上凸，它们的逐点最大值也凸。对最大值函数在 [0,1000] 上三分，收缩到最小值附近，再输出函数值。

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
