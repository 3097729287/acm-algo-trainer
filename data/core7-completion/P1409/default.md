## P1409 骰子

原题：[P1409](https://www.luogu.com.cn/problem/P1409)

### 思路

令 P[n][m] 表示胜率。m>1 时，P[n][m]=P[n][m−1]/2+P[n−1][m−1]/3；队首胜率满足 P[n][1]=1/6+P[n][n]/2。把后一条代入整行递推，解出首项后顺次计算。

### 复杂度

时间 O(n²)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<double> previous(n + 1), current(n + 1), constant(n + 1);
    previous[1] = 1;
    for (int size = 2; size <= n; size++) {
        constant[1] = 0;
        double coefficient = 1;
        for (int position = 2; position <= size; position++) {
            coefficient *= 0.5;
            constant[position] = constant[position - 1] * 0.5 + previous[position - 1] / 3.0;
        }
        current[1] = (1.0 / 6 + constant[size] * 0.5) / (1 - coefficient * 0.5);
        for (int position = 2; position <= size; position++)
            current[position] = current[position - 1] * 0.5 + previous[position - 1] / 3.0;
        previous.swap(current);
    }
    cout << fixed << setprecision(9) << previous[m] << '\n';

    return 0;
}
```

### 实现提醒

单人胜率为 1；转队尾不减少人数；出队与轮转概率分别为 1/3 和 1/2。
